import { useBranding } from "../../lib/branding";
import { Logo } from "./Logo";

/** Logo de marque : celui du client (plan Professional) sinon le logo Opsora. */
export function BrandLogo({ className = "h-8 w-8" }: { className?: string }) {
  const { branding } = useBranding();
  if (branding.logo_url) {
    return (
      <img
        src={branding.logo_url}
        alt={branding.display_name}
        className={`${className} shrink-0 rounded-lg object-contain`}
      />
    );
  }
  return <Logo className={className} />;
}
