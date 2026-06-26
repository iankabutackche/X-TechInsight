import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

const markdownStyles = {
  lineHeight: 1.7,
  color: '#ececec',
}

function MessageMarkdown({ content }) {
  if (!content) {
    return null
  }

  return (
    <div style={markdownStyles}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const codeText = String(children).replace(/\n$/, '')

            if (!inline && match) {
              return (
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{
                    borderRadius: '8px',
                    fontSize: '13px',
                    margin: '12px 0',
                  }}
                  {...props}
                >
                  {codeText}
                </SyntaxHighlighter>
              )
            }

            return (
              <code
                style={{
                  background: '#2f2f2f',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                }}
                {...props}
              >
                {children}
              </code>
            )
          },
          p({ children }) {
            return <p style={{ margin: '0 0 12px' }}>{children}</p>
          },
          ul({ children }) {
            return <ul style={{ paddingLeft: '20px', margin: '0 0 12px' }}>{children}</ul>
          },
          ol({ children }) {
            return <ol style={{ paddingLeft: '20px', margin: '0 0 12px' }}>{children}</ol>
          },
          h1({ children }) {
            return <h1 style={{ fontSize: '22px', margin: '0 0 12px' }}>{children}</h1>
          },
          h2({ children }) {
            return <h2 style={{ fontSize: '18px', margin: '0 0 10px' }}>{children}</h2>
          },
          h3({ children }) {
            return <h3 style={{ fontSize: '16px', margin: '0 0 8px' }}>{children}</h3>
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MessageMarkdown
