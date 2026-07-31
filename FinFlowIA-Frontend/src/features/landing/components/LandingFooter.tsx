import { Link } from "react-router-dom";
import { Mail } from "lucide-react";
import { FOOTER_LINKS } from "@/features/landing/data/landing-content";

export function LandingFooter() {
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
              Gestión financiera inteligente para pequeños negocios.
            </p>
            <a
              href="mailto:hola@finflowia.app"
              className="mt-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              hola@finflowia.app
            </a>
          </div>

          <FooterColumn title="Producto" links={FOOTER_LINKS.producto} />
          <FooterColumn title="Cuenta" links={FOOTER_LINKS.cuenta} />
          <FooterColumn title="Legal" links={FOOTER_LINKS.legal} />
        </div>

        <div className="mt-12 border-t border-border pt-6 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} FinFlowIA. Todos los derechos reservados.</p>
        </div>
      </div>
    </footer>
  );
}

interface FooterColumnProps {
  title: string;
  links: readonly { label: string; href: string }[];
}

function FooterColumn({ title, links }: FooterColumnProps) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <ul className="mt-4 space-y-3">
        {links.map((link) => (
          <li key={link.label}>
            {link.href.startsWith("/") ? (
              <Link to={link.href} className="text-sm text-muted-foreground hover:text-foreground">
                {link.label}
              </Link>
            ) : (
              <a href={link.href} className="text-sm text-muted-foreground hover:text-foreground">
                {link.label}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
