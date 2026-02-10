import { Component, type ReactNode } from 'react'
import './ErrorBoundary.css'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.setState({ error, errorInfo })
    
    // Log to error tracking service (if configured)
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      return (
        this.props.fallback || (
          <div className="error-boundary" role="alert" aria-live="assertive">
            <div className="error-boundary-content">
              <div className="error-icon">⚠️</div>
              <h2>Something went wrong</h2>
              <p className="error-message">
                The application encountered an unexpected error. We've logged the issue
                and recommend refreshing the page.
              </p>
              
              {this.state.error && (
                <details className="error-details">
                  <summary>Error details (for developers)</summary>
                  <pre className="error-stack">
                    {this.state.error.toString()}
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </details>
              )}
              
              <div className="error-actions">
                <button 
                  onClick={this.handleReset}
                  className="button-primary"
                >
                  🔄 Reload Application
                </button>
                <button 
                  onClick={() => window.history.back()}
                  className="button-secondary"
                >
                  ← Go Back
                </button>
              </div>
              
              <p className="error-hint">
                If the problem persists, please check the console for more details
                or contact support.
              </p>
            </div>
          </div>
        )
      )
    }

    return this.props.children
  }
}

// Error boundary specifically for smaller component sections
export class ComponentErrorBoundary extends Component<Props & { onReset?: () => void }, State> {
  constructor(props: Props & { onReset?: () => void }) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ComponentErrorBoundary caught an error:', error, errorInfo)
    this.setState({ error, errorInfo })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    this.props.onReset?.()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="component-error" role="alert">
          <span className="component-error-icon">⚠️</span>
          <span className="component-error-text">Component failed to load</span>
          <button 
            onClick={this.handleReset}
            className="component-error-retry"
            title="Retry loading this component"
          >
            Retry
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
