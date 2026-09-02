import { useTranslation } from "react-i18next";
import { Languages } from "lucide-react";
import { Button } from "@/shared/components/ui/Button";

const LANGUAGES = ["es", "en"] as const;

/**
 * Minimal ES/EN toggle. i18next-browser-languagedetector persists the
 * choice to localStorage automatically (see shared/i18n/index.ts).
 */
export function LanguageSwitcher() {
  const { i18n, t } = useTranslation("common");
  const current = i18n.resolvedLanguage === "en" ? "en" : "es";

  const switchLanguage = () => {
    const next = LANGUAGES.find((lng) => lng !== current) ?? "es";
    void i18n.changeLanguage(next);
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={switchLanguage}
      aria-label={t("language.label")}
      title={t("language.label")}
      className="gap-1.5"
    >
      <Languages className="h-4 w-4" />
      <span className="uppercase">{current}</span>
    </Button>
  );
}
