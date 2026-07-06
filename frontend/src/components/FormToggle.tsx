interface Props {
  id: string;
  checked: boolean;
  onChange: () => void;
  label: string;
  tone?: 'default' | 'gold';
}

export const FormToggle = ({ id, checked, onChange, label, tone = 'default' }: Props) => (
  <button
    type="button"
    id={id}
    role="switch"
    aria-checked={checked}
    onClick={onChange}
    className="w-full flex items-center justify-between gap-3 bg-background rounded-2xl px-4 py-3 border border-inputBorder hover:bg-card3/20 transition"
  >
    <span className={`text-sm font-ui text-start ${tone === 'gold' ? 'text-gold' : 'text-textPrimary'}`}>
      {label}
    </span>
    <span className={`relative w-12 h-7 rounded-full transition-colors flex-shrink-0 ${checked ? 'bg-gold' : 'bg-card3'}`}>
      <span className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow transition-all ${checked ? 'right-1' : 'left-1'}`} />
    </span>
  </button>
);
