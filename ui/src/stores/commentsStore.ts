import { create } from 'zustand'

// ==================== TYPES ====================

export interface Comment {
  id: string
  nodeId: string
  text: string
  author: string
  authorColor: string
  createdAt: string
  resolved: boolean
  resolvedAt?: string
  resolvedBy?: string
  replies: Reply[]
}

export interface Reply {
  id: string
  text: string
  author: string
  authorColor: string
  createdAt: string
}

export interface CommentsState {
  comments: Comment[]
  commentsPanelOpen: boolean
  selectedNodeId: string | null
  
  // Actions
  toggleCommentsPanel: () => void
  openCommentsForNode: (nodeId: string) => void
  closeCommentsPanel: () => void
  addComment: (nodeId: string, text: string, author?: string) => void
  addReply: (commentId: string, text: string, author?: string) => void
  resolveComment: (commentId: string, author?: string) => void
  unresolveComment: (commentId: string) => void
  deleteComment: (commentId: string) => void
  getCommentsForNode: (nodeId: string) => Comment[]
  getUnresolvedCount: (nodeId?: string) => number
  getAllUnresolvedCount: () => number
}

// Author colors for visual distinction
const AUTHOR_COLORS = ['#4a9eff', '#4caf50', '#ff9800', '#9c27b0', '#ef4444', '#00bcd4']

// Mock initial comments
const generateMockComments = (): Comment[] => [
  {
    id: 'comment-1',
    nodeId: 'node-1',
    text: 'This scene needs more tension. Consider adding a ticking clock element.',
    author: 'Editor',
    authorColor: AUTHOR_COLORS[0],
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    resolved: false,
    replies: [
      {
        id: 'reply-1',
        text: 'Good point! I\'ll add a deadline to the dialogue.',
        author: 'Writer',
        authorColor: AUTHOR_COLORS[1],
        createdAt: new Date(Date.now() - 43200000).toISOString(),
      },
    ],
  },
  {
    id: 'comment-2',
    nodeId: 'node-1',
    text: 'The character voice feels inconsistent here.',
    author: 'Reviewer',
    authorColor: AUTHOR_COLORS[2],
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    resolved: true,
    resolvedAt: new Date(Date.now() - 86400000).toISOString(),
    resolvedBy: 'Writer',
    replies: [],
  },
  {
    id: 'comment-3',
    nodeId: 'node-5',
    text: 'This is the key turning point. Make sure to emphasize the emotional impact.',
    author: 'Editor',
    authorColor: AUTHOR_COLORS[0],
    createdAt: new Date(Date.now() - 259200000).toISOString(),
    resolved: false,
    replies: [],
  },
]

// ==================== STORE IMPLEMENTATION ====================

export const useCommentsStore = create<CommentsState>((set, get) => ({
  // ==================== INITIAL STATE ====================
  comments: generateMockComments(),
  commentsPanelOpen: false,
  selectedNodeId: null,
  
  // ==================== PANEL ACTIONS ====================
  toggleCommentsPanel: () => {
    set(state => ({ commentsPanelOpen: !state.commentsPanelOpen }))
  },
  
  openCommentsForNode: (nodeId) => {
    set({
      commentsPanelOpen: true,
      selectedNodeId: nodeId,
    })
  },
  
  closeCommentsPanel: () => {
    set({
      commentsPanelOpen: false,
      selectedNodeId: null,
    })
  },
  
  // ==================== COMMENT ACTIONS ====================
  addComment: (nodeId, text, author = 'User') => {
    const newComment: Comment = {
      id: `comment-${Date.now()}`,
      nodeId,
      text,
      author,
      authorColor: AUTHOR_COLORS[Math.floor(Math.random() * AUTHOR_COLORS.length)],
      createdAt: new Date().toISOString(),
      resolved: false,
      replies: [],
    }
    
    set(state => ({
      comments: [newComment, ...state.comments],
    }))
  },
  
  addReply: (commentId, text, author = 'User') => {
    const newReply: Reply = {
      id: `reply-${Date.now()}`,
      text,
      author,
      authorColor: AUTHOR_COLORS[Math.floor(Math.random() * AUTHOR_COLORS.length)],
      createdAt: new Date().toISOString(),
    }
    
    set(state => ({
      comments: state.comments.map(c =>
        c.id === commentId
          ? { ...c, replies: [...c.replies, newReply] }
          : c
      ),
    }))
  },
  
  resolveComment: (commentId, author = 'User') => {
    set(state => ({
      comments: state.comments.map(c =>
        c.id === commentId
          ? {
              ...c,
              resolved: true,
              resolvedAt: new Date().toISOString(),
              resolvedBy: author,
            }
          : c
      ),
    }))
  },
  
  unresolveComment: (commentId) => {
    set(state => ({
      comments: state.comments.map(c =>
        c.id === commentId
          ? { ...c, resolved: false, resolvedAt: undefined, resolvedBy: undefined }
          : c
      ),
    }))
  },
  
  deleteComment: (commentId) => {
    set(state => ({
      comments: state.comments.filter(c => c.id !== commentId),
    }))
  },
  
  // ==================== HELPERS ====================
  getCommentsForNode: (nodeId) => {
    return get().comments
      .filter(c => c.nodeId === nodeId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  },
  
  getUnresolvedCount: (nodeId) => {
    if (nodeId) {
      return get().comments.filter(c => c.nodeId === nodeId && !c.resolved).length
    }
    return get().comments.filter(c => !c.resolved).length
  },
  
  getAllUnresolvedCount: () => {
    return get().comments.filter(c => !c.resolved).length
  },
}))
