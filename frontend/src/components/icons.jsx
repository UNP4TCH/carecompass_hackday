// Small inline SVG icons. Decorative: always aria-hidden.

const base = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": "true",
  focusable: "false",
};

export function ArrowRight(props) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export function Check(props) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12.5l4.5 4.5L19 7.5" />
    </svg>
  );
}

export function Alert(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3.5l9.5 16.5h-19L12 3.5z" />
      <path d="M12 10v4.5M12 17.4v.1" />
    </svg>
  );
}

export function Clock(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3.5 2" />
    </svg>
  );
}

export function MapPin(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0113 0c0 5.4-6.5 11-6.5 11z" />
      <circle cx="12" cy="10" r="2.3" />
    </svg>
  );
}

export function Refresh(props) {
  return (
    <svg {...base} {...props}>
      <path d="M20 11a8 8 0 10-2.3 5.7" />
      <path d="M20 4.5V11h-6.5" />
    </svg>
  );
}

export function Restart(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 12a8 8 0 112.3 5.7" />
      <path d="M4 19.5V13h6.5" />
    </svg>
  );
}

export function SeverityIcon({ name, ...props }) {
  if (name === "alert") return <Alert {...props} />;
  if (name === "clock") return <Clock {...props} />;
  if (name === "check") return <Check {...props} />;
  return null;
}

export function FileText(props) {
  return (
    <svg {...base} {...props}>
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
    </svg>
  );
}

export function UploadCloud(props) {
  return (
    <svg {...base} {...props}>
      <path d="M16 16l-4-4-4 4M12 12v9" />
      <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
    </svg>
  );
}

export function XIcon(props) {
  return (
    <svg {...base} {...props}>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

