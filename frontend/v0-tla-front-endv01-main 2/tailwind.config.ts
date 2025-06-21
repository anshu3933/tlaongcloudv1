import type { Config } from "tailwindcss"
import { fontFamily } from "tailwindcss/defaultTheme"

const config: Config = {
  darkMode: ["class"],
  content: [
    "app/**/*.{ts,tsx}",
    "components/**/*.{ts,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",

        primary: {
          DEFAULT: "#14b8a6" /* Base Teal */,
          lighter: "#5eead4" /* Lighter Teal */,
          lightest: "#ccfbf1" /* Lightest Teal */,
          darker: "#0d9488" /* Darker Teal */,
          darkest: "#0f766e" /* Darkest Teal */,
          foreground: "hsl(var(--primary-foreground))",
        },

        secondary: {
          DEFAULT: "#3b82f6" /* Base Blue */,
          lighter: "#93c5fd" /* Lighter Blue */,
          lightest: "#dbeafe" /* Lightest Blue */,
          darker: "#2563eb" /* Darker Blue */,
          darkest: "#1d4ed8" /* Darkest Blue */,
          foreground: "hsl(var(--secondary-foreground))",
        },

        tertiary: {
          DEFAULT: "#8b5cf6" /* Base Purple */,
          lighter: "#c4b5fd" /* Lighter Purple */,
          lightest: "#ede9fe" /* Lightest Purple */,
          darker: "#7c3aed" /* Darker Purple */,
          darkest: "#6d28d9" /* Darkest Purple */,
          foreground: "hsl(var(--tertiary-foreground))",
        },

        success: {
          DEFAULT: "#10b981" /* Success */,
          light: "#a7f3d0" /* Light Success */,
          foreground: "hsl(var(--success-foreground))",
        },

        warning: {
          DEFAULT: "#f59e0b" /* Warning */,
          light: "#fef3c7" /* Light Warning */,
          foreground: "hsl(var(--warning-foreground))",
        },

        error: {
          DEFAULT: "#dc2626" /* Error (Darkened) */,
          light: "#fee2e2" /* Light Error */,
          foreground: "hsl(var(--error-foreground))",
        },

        info: {
          DEFAULT: "#3b82f6" /* Info (Same as Secondary) */,
          light: "#dbeafe" /* Light Info */,
          foreground: "hsl(var(--info-foreground))",
        },

        neutral: {
          DEFAULT: "#9ca3af" /* Neutral */,
          light: "#f3f4f6" /* Light Neutral */,
        },

        gray: {
          100: "#f9fafb" /* Gray 100 */,
          200: "#f3f4f6" /* Gray 200 */,
          300: "#e5e7eb" /* Gray 300 */,
          400: "#d1d5db" /* Gray 400 */,
          500: "#9ca3af" /* Gray 500 */,
          600: "#6b7280" /* Gray 600 */,
          700: "#4b5563" /* Gray 700 */,
          800: "#374151" /* Gray 800 */,
          900: "#1f2937" /* Gray 900 */,
        },

        destructive: {
          DEFAULT: "hsl(var(--error))",
          foreground: "hsl(var(--error-foreground))",
        },

        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },

        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },

        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },

        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", ...fontFamily.sans],
      },
      boxShadow: {
        xs: "0 1px 2px rgba(0, 0, 0, 0.05)",
        sm: "0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)",
        md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
        lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
      },
      transitionDuration: {
        "50": "50ms",
        "150": "150ms",
        "250": "250ms",
        "350": "350ms",
        "450": "450ms",
      },
      transitionProperty: {
        height: "height",
        spacing: "margin, padding",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
