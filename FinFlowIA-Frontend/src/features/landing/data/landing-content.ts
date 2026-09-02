import type { LucideIcon } from "lucide-react";
import {
  BadgeCheck,
  BarChart3,
  FileDown,
  Layers,
  ShieldCheck,
  Smartphone,
  Sparkles,
  UserPlus,
  Wallet,
} from "lucide-react";

/**
 * Structural data only — no display copy here. Titles/descriptions live in
 * the "landing" i18n namespace (src/shared/i18n/locales/{es,en}/landing.json),
 * keyed by the stable `id` below, so switching language never requires
 * touching this file. See the components in this folder for
 * `t(`features.items.${id}.title`)`-style lookups.
 */

export interface Feature {
  id: string;
  icon: LucideIcon;
}

export const FEATURES: Feature[] = [
  { id: "ai-categorization", icon: Sparkles },
  { id: "realtime-dashboard", icon: BarChart3 },
  { id: "exportable-reports", icon: FileDown },
  { id: "custom-categories", icon: Layers },
  { id: "bank-grade-security", icon: ShieldCheck },
  { id: "responsive-anywhere", icon: Smartphone },
];

export interface Step {
  id: string;
  icon: LucideIcon;
}

export const STEPS: Step[] = [
  { id: "create-account", icon: UserPlus },
  { id: "log-transactions", icon: Wallet },
  { id: "ai-categorizes", icon: Sparkles },
  { id: "clear-dashboard", icon: BarChart3 },
];

export interface TrustIndicator {
  id: string;
  icon: LucideIcon;
}

/**
 * FinFlowIA todavía no tiene clientes públicos, así que en vez de inventar
 * testimonios con nombres y fotos falsas, esta sección muestra señales de
 * confianza reales sobre cómo está construido el producto. Reemplazar por
 * testimonios reales cuando existan.
 */
export const TRUST_INDICATORS: TrustIndicator[] = [
  { id: "powered-by-claude", icon: Sparkles },
  { id: "end-to-end-encryption", icon: ShieldCheck },
  { id: "built-for-small-business", icon: BadgeCheck },
];

export const FAQ_IDS = [
  "credit-card",
  "how-ai-works",
  "data-security",
  "export-reports",
  "any-business",
  "mobile-usage",
] as const;

export const NAV_LINKS = [
  { id: "features", href: "#features" },
  { id: "howItWorks", href: "#how-it-works" },
  { id: "faq", href: "#faq" },
] as const;

export const FOOTER_LINKS = {
  product: [
    { id: "features", href: "#features" },
    { id: "howItWorks", href: "#how-it-works" },
    { id: "faq", href: "#faq" },
  ],
  account: [
    { id: "login", href: "/login" },
    { id: "createAccount", href: "/register" },
  ],
  legal: [
    { id: "privacy", href: "#" },
    { id: "terms", href: "#" },
  ],
} as const;
