import { Link } from "react-router-dom";
import { Mail } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import { FOOTER_LINKS } from "@/features/landing/data/landing-content";

export function LandingFooter() {
  const { t } = useTranslation("landing");

  return (
    <footer className="border-t border-border bg-muted/30">
      <div className="container py-12">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <Link to="/" className="flex items-center gap-2 font-bold text-foreground">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-xs font-bold text-primary-foreground">
                FF
              </span>
              <span>FinFlowIA</span>
            </Link>
            <p className="mt-3 text-sm text-muted-foreground">
              {t("footer.tagline")}
            </p>
            <a
              href="mailto:hola@finflowia.app"
              className="mt-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              hola@finflowia.app
            </a>
          </div>

          <FooterColumn title={t("footer.columns.product")} links={FOOTER_LINKS.product} t={t} />
          <FooterColumn title={t("footer.columns.account")} links={FOOTER_LINKS.account} t={t} />
          <FooterColumn title={t("footer.columns.legal")} links={FOOTER_LINKS.legal} t={t} />
        </div>

        <div className="mt-12 border-t border-border pt-6 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} FinFlowIA. {t("footer.rights")}</p>
        </div>
      </div>
    </footer>
  );
}

interface FooterColumnProps {
  title: string;
  links: readonly { id: string; href: string }[];
  t: TFunction<"landing">;
}

function FooterColumn({ title, links, t }: FooterColumnProps) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <ul className="mt-4 space-y-3">
        {links.map((link) => (
          <li key={link.id}>
            {link.href.startsWith("/") ? (
              <Link to={link.href} className="text-sm text-muted-foreground hover:text-foreground">
                {t(`footer.links.${link.id}`)}
              </Link>
            ) : (
              <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground">
                {t(`footer.links.${link.id}`)}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
