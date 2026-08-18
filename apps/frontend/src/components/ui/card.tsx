import * as React from "react"

export const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = "", ...props }, ref) => (
    <div
      ref={ref}
      className={`surface-card p-5 ${className}`}
      {...props}
    />
  )
)
Card.displayName = "Card"
