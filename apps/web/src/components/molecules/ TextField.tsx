import { useState } from 'react'

import { Input } from '../atoms/Input'
import { Field } from './Field'
import React from 'react'

type TextFieldProps = {
  label: string
  type?: 'text' | 'email' | 'password'
  value: string
  onChange: (value: string) => void
  placeholder?: string
  hint?: string
  error?: string
}

export function TextField({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  hint,
  error,
}: TextFieldProps) {
  const [visible, setVisible] = useState(false)
  const isPassword = type === 'password'

  return (
    <Field label={label} hint={hint} error={error}>
      {({ id, describedBy, invalid }) => (
        <div className="relative">
          <Input
            id={id}
            type={isPassword && visible ? 'text' : type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            aria-invalid={invalid || undefined}
            aria-describedby={describedBy}
            className={isPassword ? 'pr-24' : undefined}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setVisible((v) => !v)}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-muted"
            >
              {visible ? 'Masquer' : 'Afficher'}
            </button>
          )}
        </div>
      )}
    </Field>
  )
}