import { useState, useEffect, useCallback, useRef } from 'react'
import { useAppStore } from '../store'
import './RichTextEditor.css'

interface RichTextEditorProps {
  nodeId: string
  initialContent?: string
  onSave?: () => void
  onCancel?: () => void
}

export function RichTextEditor({ nodeId, initialContent = '', onSave, onCancel }: RichTextEditorProps) {
  const { 
    nodes, 
    updateNodeContent, 
    saveNodeVersion, 
    stopEditingNode,
    loading,
  } = useAppStore()
  
  const node = nodes.find(n => n.id === nodeId)
  const [content, setContent] = useState(initialContent || node?.content.text || '')
  const [wordCount, setWordCount] = useState(0)
  const [showPreview, setShowPreview] = useState(false)
  const [isDirty, setIsDirty] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const autoSaveRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  
  // Calculate word count
  useEffect(() => {
    const count = content.trim().split(/\s+/).filter(w => w.length > 0).length
    setWordCount(count)
  }, [content])
  
  // Auto-focus textarea
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])
  
  // Auto-save draft every 5 seconds when dirty
  useEffect(() => {
    if (isDirty && content) {
      if (autoSaveRef.current) clearTimeout(autoSaveRef.current)
      autoSaveRef.current = setTimeout(() => {
        handleSave(false) // Save without closing
      }, 5000)
    }
    return () => {
      if (autoSaveRef.current) clearTimeout(autoSaveRef.current)
    }
  }, [content, isDirty, nodeId])
  
  const handleSave = useCallback(async (closeAfter = true) => {
    if (!nodeId) return
    
    await updateNodeContent(nodeId, content)
    await saveNodeVersion(nodeId)
    setIsDirty(false)
    
    if (closeAfter) {
      stopEditingNode()
      onSave?.()
    }
  }, [content, nodeId, updateNodeContent, saveNodeVersion, stopEditingNode, onSave])
  
  const handleCancel = useCallback(() => {
    if (isDirty && !confirm('Discard unsaved changes?')) return
    stopEditingNode()
    onCancel?.()
  }, [isDirty, stopEditingNode, onCancel])
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault()
      handleSave(false)
    }
    // Escape to cancel
    if (e.key === 'Escape') {
      e.preventDefault()
      handleCancel()
    }
  }
  
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value)
    setIsDirty(true)
  }
  
  // Simple markdown preview
  const renderPreview = (text: string) => {
    return text
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      .replace(/`([^`]+)`/gim, '<code>$1</code>')
      .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
      .replace(/^(\*|\-|\d\.) (.*$)/gim, '<li>$2</li>')
      .replace(/\n/gim, '<br />')
  }
  
  const insertMarkdown = (before: string, after: string = '') => {
    const textarea = textareaRef.current
    if (!textarea) return
    
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selected = content.substring(start, end)
    const newContent = content.substring(0, start) + before + selected + after + content.substring(end)
    
    setContent(newContent)
    setIsDirty(true)
    
    // Restore focus and selection
    setTimeout(() => {
      textarea.focus()
      const newCursor = start + before.length + selected.length
      textarea.setSelectionRange(newCursor, newCursor)
    }, 0)
  }
  
  if (!node) return null
  
  return (
    <div className="rich-text-editor" role="dialog" aria-label="Edit node content">
      <div className="editor-header">
        <h3 className="editor-title">
          Editing: {node.label}
          {isDirty && <span className="dirty-indicator">●</span>}
        </h3>
        <div className="editor-meta">
          <span className="word-count">{wordCount} words</span>
          <span className="version-info">v{node.content.version + 1}</span>
        </div>
      </div>
      
      <div className="editor-toolbar" role="toolbar" aria-label="Text formatting">
        <button 
          onClick={() => insertMarkdown('**', '**')}
          title="Bold (Ctrl+B)"
          aria-label="Bold"
        >
          <strong>B</strong>
        </button>
        <button 
          onClick={() => insertMarkdown('*', '*')}
          title="Italic (Ctrl+I)"
          aria-label="Italic"
        >
          <em>I</em>
        </button>
        <button 
          onClick={() => insertMarkdown('# ', '')}
          title="Heading"
          aria-label="Heading"
        >
          H1
        </button>
        <button 
          onClick={() => insertMarkdown('## ', '')}
          title="Subheading"
          aria-label="Subheading"
        >
          H2
        </button>
        <button 
          onClick={() => insertMarkdown('> ', '')}
          title="Quote"
          aria-label="Quote"
        >
          "❝
        </button>
        <button 
          onClick={() => insertMarkdown('`', '`')}
          title="Code"
          aria-label="Code"
        >
          {'<>'}
        </button>
        <button 
          onClick={() => insertMarkdown('\n- ', '')}
          title="List item"
          aria-label="List item"
        >
          • List
        </button>
        <div className="toolbar-divider" />
        <button 
          onClick={() => setShowPreview(!showPreview)}
          className={showPreview ? 'active' : ''}
          title="Toggle preview"
          aria-label="Toggle preview"
          aria-pressed={showPreview}
        >
          👁 Preview
        </button>
      </div>
      
      <div className={`editor-content ${showPreview ? 'with-preview' : ''}`}>
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Write your scene content here..."
          className="editor-textarea"
          aria-label="Content editor"
          disabled={loading.content}
        />
        
        {showPreview && (
          <div 
            className="editor-preview"
            dangerouslySetInnerHTML={{ __html: renderPreview(content) }}
            aria-label="Content preview"
          />
        )}
      </div>
      
      {loading.content && (
        <div className="editor-saving" role="status">
          <span className="spinner" />
          Saving...
        </div>
      )}
      
      <div className="editor-footer">
        <div className="editor-shortcuts">
          <kbd>Ctrl</kbd>+<kbd>S</kbd> Save • 
          <kbd>Esc</kbd> Cancel •
          Auto-saves every 5s
        </div>
        <div className="editor-actions">
          <button 
            onClick={handleCancel}
            className="button-secondary"
            disabled={loading.content}
          >
            Cancel
          </button>
          <button 
            onClick={() => handleSave(true)}
            className="button-primary"
            disabled={loading.content || !isDirty}
          >
            {loading.content ? 'Saving...' : 'Save & Close'}
          </button>
        </div>
      </div>
    </div>
  )
}
