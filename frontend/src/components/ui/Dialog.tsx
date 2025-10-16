import { ReactNode } from 'react'

interface DialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: ReactNode
}

interface DialogContentProps {
  children: ReactNode
  className?: string
}

interface DialogHeaderProps {
  children: ReactNode
}

interface DialogTitleProps {
  children: ReactNode
  className?: string
}

interface DialogDescriptionProps {
  children: ReactNode
}

interface DialogFooterProps {
  children: ReactNode
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />
      {/* Dialog Content */}
      <div className="relative z-50 w-full flex items-center justify-center min-h-full py-4">{children}</div>
    </div>
  )
}

export function DialogContent({ children, className = '' }: DialogContentProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow-xl max-w-md w-full mx-auto p-6 max-h-[90vh] overflow-y-auto ${className}`}
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </div>
  )
}

export function DialogHeader({ children }: DialogHeaderProps) {
  return <div className="mb-4">{children}</div>
}

export function DialogTitle({ children, className = '' }: DialogTitleProps) {
  return <h2 className={`text-xl font-semibold text-gray-900 ${className}`}>{children}</h2>
}

export function DialogDescription({ children }: DialogDescriptionProps) {
  return <p className="text-sm text-gray-600 mt-2">{children}</p>
}

export function DialogFooter({ children }: DialogFooterProps) {
  return <div className="flex gap-3 justify-end mt-6">{children}</div>
}
