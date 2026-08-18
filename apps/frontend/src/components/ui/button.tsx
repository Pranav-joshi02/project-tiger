import * as React from "react"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost"
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "primary", ...props }, ref) => {
    const base = "inline-flex items-center justify-center rounded-lg text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-forest-500/20 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.97] px-4 py-2"
    const variants = {
      primary: "bg-forest-800 hover:bg-forest-700 text-white shadow-sm",
      secondary: "bg-gold-400 hover:bg-gold-500 text-white shadow-sm",
      outline: "border border-ink-100 hover:bg-page-200 text-ink-700 bg-white",
      ghost: "hover:bg-ink-50 text-ink-600",
    }
    return (
      <button
        ref={ref}
        className={`${base} ${variants[variant]} ${className}`}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"
