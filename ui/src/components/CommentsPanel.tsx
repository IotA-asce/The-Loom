import { useState } from 'react'
import { useCommentsStore } from '../stores/commentsStore'
import { useAppStore } from '../store'
import './CommentsPanel.css'

interface CommentsPanelProps {
  isOpen: boolean
  onClose: () => void
  nodeId?: string
}

export function CommentsPanel({ isOpen, onClose, nodeId }: CommentsPanelProps) {
  const {
    selectedNodeId,
    addComment,
    addReply,
    resolveComment,
    unresolveComment,
    deleteComment,
    getCommentsForNode,
    getUnresolvedCount,
  } = useCommentsStore()
  
  const { nodes } = useAppStore()
  const [newComment, setNewComment] = useState('')
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [replyText, setReplyText] = useState('')
  const [showResolved, setShowResolved] = useState(false)
  
  if (!isOpen) return null
  
  const targetNodeId = nodeId || selectedNodeId
  const nodeComments = targetNodeId ? getCommentsForNode(targetNodeId) : []
  const unresolvedCount = targetNodeId ? getUnresolvedCount(targetNodeId) : 0
  
  const node = nodes.find(n => n.id === targetNodeId)
  
  const handleAddComment = () => {
    if (!targetNodeId || !newComment.trim()) return
    addComment(targetNodeId, newComment.trim())
    setNewComment('')
  }
  
  const handleAddReply = (commentId: string) => {
    if (!replyText.trim()) return
    addReply(commentId, replyText.trim())
    setReplyText('')
    setReplyingTo(null)
  }
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return date.toLocaleDateString()
  }
  
  const filteredComments = showResolved
    ? nodeComments
    : nodeComments.filter(c => !c.resolved)
  
  return (
    <div className="comments-overlay" onClick={onClose}>
      <div className="comments-panel" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="comments-header">
          <div className="comments-title">
            <h2>💬 Comments</h2>
            {node && (
              <span className="node-name">on "{node.label}"</span>
            )}
          </div>
          <div className="comments-meta">
            {unresolvedCount > 0 && (
              <span className="unresolved-badge">{unresolvedCount} open</span>
            )}
            <button className="close-btn" onClick={onClose}>×</button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="comments-filters">
          <button
            className={`filter-btn ${!showResolved ? 'active' : ''}`}
            onClick={() => setShowResolved(false)}
          >
            Open ({unresolvedCount})
          </button>
          <button
            className={`filter-btn ${showResolved ? 'active' : ''}`}
            onClick={() => setShowResolved(true)}
          >
            All ({nodeComments.length})
          </button>
        </div>
        
        {/* New Comment */}
        {targetNodeId && (
          <div className="new-comment">
            <textarea
              placeholder="Add a comment..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              rows={3}
            />
            <button
              className="add-comment-btn"
              onClick={handleAddComment}
              disabled={!newComment.trim()}
            >
              Add Comment
            </button>
          </div>
        )}
        
        {/* Comments List */}
        <div className="comments-list">
          {filteredComments.length > 0 ? (
            filteredComments.map(comment => (
              <div
                key={comment.id}
                className={`comment-thread ${comment.resolved ? 'resolved' : ''}`}
              >
                {/* Main Comment */}
                <div className="comment-main">
                  <div
                    className="comment-avatar"
                    style={{ backgroundColor: comment.authorColor }}
                  >
                    {comment.author[0].toUpperCase()}
                  </div>
                  
                  <div className="comment-content">
                    <div className="comment-header">
                      <span className="comment-author">{comment.author}</span>
                      <span className="comment-time">
                        {formatDate(comment.createdAt)}
                      </span>
                      {comment.resolved && (
                        <span className="resolved-badge">
                          ✓ Resolved
                        </span>
                      )}
                    </div>
                    
                    <p className="comment-text">{comment.text}</p>
                    
                    {/* Comment Actions */}
                    <div className="comment-actions">
                      {!comment.resolved ? (
                        <>
                          <button
                            className="action-link"
                            onClick={() => setReplyingTo(comment.id)}
                          >
                            Reply
                          </button>
                          <button
                            className="action-link resolve"
                            onClick={() => resolveComment(comment.id)}
                          >
                            ✓ Resolve
                          </button>
                        </>
                      ) : (
                        <button
                          className="action-link unresolve"
                          onClick={() => unresolveComment(comment.id)}
                        >
                          ↩ Reopen
                        </button>
                      )}
                      <button
                        className="action-link delete"
                        onClick={() => {
                          if (confirm('Delete this comment?')) {
                            deleteComment(comment.id)
                          }
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Reply Input */}
                {replyingTo === comment.id && (
                  <div className="reply-input">
                    <textarea
                      placeholder="Write a reply..."
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      rows={2}
                      autoFocus
                    />
                    <div className="reply-actions">
                      <button
                        className="cancel-btn"
                        onClick={() => {
                          setReplyingTo(null)
                          setReplyText('')
                        }}
                      >
                        Cancel
                      </button>
                      <button
                        className="submit-btn"
                        onClick={() => handleAddReply(comment.id)}
                        disabled={!replyText.trim()}
                      >
                        Reply
                      </button>
                    </div>
                  </div>
                )}
                
                {/* Replies */}
                {comment.replies.length > 0 && (
                  <div className="replies-list">
                    {comment.replies.map(reply => (
                      <div key={reply.id} className="reply-item">
                        <div
                          className="reply-avatar"
                          style={{ backgroundColor: reply.authorColor }}
                        >
                          {reply.author[0].toUpperCase()}
                        </div>
                        <div className="reply-content">
                          <div className="reply-header">
                            <span className="reply-author">{reply.author}</span>
                            <span className="reply-time">
                              {formatDate(reply.createdAt)}
                            </span>
                          </div>
                          <p className="reply-text">{reply.text}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Resolution Info */}
                {comment.resolved && comment.resolvedBy && (
                  <div className="resolution-info">
                    Resolved by {comment.resolvedBy} • {formatDate(comment.resolvedAt!)}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="empty-comments">
              <span className="empty-icon">💬</span>
              <p>{showResolved ? 'No comments yet' : 'No open comments'}</p>
              {!showResolved && nodeComments.some(c => c.resolved) && (
                <button
                  className="show-resolved-link"
                  onClick={() => setShowResolved(true)}
                >
                  Show resolved comments
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Comment indicator for nodes
export function CommentIndicator({ nodeId }: { nodeId: string }) {
  const count = useCommentsStore(state => state.getUnresolvedCount(nodeId))
  
  if (count === 0) return null
  
  return (
    <div className="node-comment-indicator">
      <span>💬</span>
      <span className="count">{count}</span>
    </div>
  )
}
