const PATHS = {
  map: 'M3 4h7v7H3z M14 4h7v7h-7z M3 15h7v6H3z M14 15h7v6h-7z',
  car: 'M5 17H3v-6l2-6h14l2 6v6h-2 M5 17h14 M5 17v3 M19 17v3 M3 11h18 M7 14h1 M16 14h1',
  user: 'M20 21v-2a7 7 0 0 0-14 0v2 M12 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8',
  arrow: 'M5 12h14 M14 7l5 5-5 5',
  plus: 'M12 5v14 M5 12h14',
  refresh: 'M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 14 6 M18 18A8 8 0 0 1 4 12',
  search: 'M10.5 3a7.5 7.5 0 1 0 0 15 7.5 7.5 0 0 0 0-15 M16 16l5 5',
  layers: 'M12 3 2 8l10 5 10-5-10-5 M2 12l10 5 10-5 M2 16l10 5 10-5',
  expand: 'M8 3H3v5 M16 3h5v5 M21 16v5h-5 M8 21H3v-5',
  bolt: 'M13 2 4 14h7l-1 8 10-13h-8l1-7',
  close: 'M6 6l12 12 M18 6 6 18',
  edit: 'm16 3 5 5-12 12-6 1 1-6L16 3 M13 6l5 5',
  exit: 'M9 4H4v16h5 M10 12h11 M16 7l5 5-5 5',
  check: 'm5 12 4 4L19 6',
  cube: 'm12 2 9 5v10l-9 5-9-5V7l9-5 M3 7l9 5 9-5 M12 12v10',
}

export default function BayIcon({ name, size = 20, ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      <path d={PATHS[name] || PATHS.map} />
    </svg>
  )
}
