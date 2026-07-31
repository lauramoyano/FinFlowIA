import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { useAuthStore } from "@/features/auth/store/auth.store";
import { buttonVariants } from "@/shared/components/ui/Button";
import { cn } from "@/shared/lib/utils";
import { NAV_LINKS } from "@/features/landing/data/landing-content";

export function LandingNavbar() {
  const [isOpen, setIsOpen] = useState(false);
  const token = useAuthStore((state) => state.token);

  const closeMenu = () => setIsOpen(false);

  // Let Escape close the mobile panel, same as any other dismissible overlay.
  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeMenu();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen]);

  return (
    <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-foreground" onClick={closeMenu}>
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
            FF
          </span>
          <span className="text-lg">FinFlowIA</span>
        </Link>

        <nav aria-label="Principal" className="hidden lg:block">
          <ul className="flex items-center gap-8 text-sm font-medium text-muted-foreground">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <a href={link.href} className="transition-colors hover:text-foreground">
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          {token ? (
            <Link to="/dashboard" className={cn(buttonVariants())}>
              Ir al dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className={cn(buttonVariants({ variant: "ghost" }))}>
                Iniciar sesión
              </Link>
              <Link to="/register" className={cn(buttonVariants())}>
                Comenzar gratis
              </Link>
            </>
          )}
        </div>

        <button
          type="button"
          className="inline-flex h-10 w-10 items-center justify-center rounded-md text-foreground transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 lg:hidden"
          aria-expanded={isOpen}
          aria-controls="mobile-menu"
          aria-label={isOpen ? "Cerrar menú" : "Abrir menú"}
          onClick={() => setIsOpen((value) => !value)}
        >
          {isOpen ? (
            <X className="h-6 w-6" aria-hidden="true" />
          ) : (
            <Menu className="h-6 w-6" aria-hidden="true" />
          )}
        </button>
      </div>

      {isOpen && (
        <nav id="mobile-menu" aria-label="Principal (móvil)" className="border-t border-border lg:hidden">
          <ul className="container flex flex-col gap-1 py-4">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  onClick={closeMenu}
                  className="block rounded-md px-2 py-2.5 text-base font-medium text-foreground hover:bg-accent"
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
          <div className="container flex flex-col gap-2 border-t border-border pb-6 pt-4">
            {token ? (
              <Link to="/dashboard" onClick={closeMenu} className={cn(buttonVariants())}>
                Ir al dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  onClick={closeMenu}
                  className={cn(buttonVariants({ variant: "outline" }))}
                >
                  Iniciar sesión
                </Link>
                <Link to="/register" onClick={closeMenu} className={cn(buttonVariants())}>
                  Comenzar gratis
                </Link>
              </>
            )}
          </div>
        </nav>
      )}
    </header>
  );
}
