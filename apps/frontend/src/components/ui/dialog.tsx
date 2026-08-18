import * as React from "react"
import { X } from "lucide-react"

interface DialogProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: React.ReactNode
}

export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl w-full max-w-lg overflow-hidden border border-ink-100 shadow-modal animate-scale-in">
        <div className="flex items-center justify-between p-5 border-b border-ink-100">
          <h3 className="text-lg font-bold text-ink-900 font-serif">{title}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-page-200 text-ink-400 hover:text-ink-700 transition-colors">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 overflow-y-auto max-h-[70vh]">
          {children}
        </div>
      </div>
    </div>
  )
}
