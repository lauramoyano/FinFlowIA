import { Moon, Sun } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useTheme } from "@/shared/providers/ThemeProvider";
import { Button } from "@/shared/components/ui/Button";

/**
 * Light/dark toggle. Renders both icons and lets CSS handle which one is
 * visible so there's no layout flash on mount.
 */
export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const { t } = useTranslation("common");
  const isDark = theme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={isDark ? t("theme.switchToLight") : t("theme.switchToDark")}
      title={isDark ? t("theme.switchToLight") : t("theme.switchToDark")}
    >
      <Sun className="h-[1.15rem] w-[1.15rem] scale-100 dark:scale-0 transition-transform" />
      <Moon className="absolute h-[1.15rem] w-[1.15rem] scale-0 dark:scale-100 transition-transform" />
      <span className="sr-only">{t("theme.toggle")}</span>
    </Button>
  );
}
