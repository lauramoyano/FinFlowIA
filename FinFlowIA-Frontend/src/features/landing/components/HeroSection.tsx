import { Link } from "react-router-dom";
import { ArrowRight, PlayCircle, Sparkles } from "lucide-react";
import { buttonVariants } from "@/shared/components/ui/Button";
import { Badge } from "@/shared/components/ui/Badge";
import { cn } from "@/shared/lib/utils";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 left-1/2 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full bg-primary/20 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
      </div>

      <div className="container grid gap-12 py-20 md:py-28 lg:grid-cols-2 lg:items-center lg:gap-8">
        <div className="mx-auto max-w-xl text-center lg:mx-0 lg:text-left">
          <Badge variant="secondary" className="mb-6 gap-1.5 py-1.5 pl-2 pr-3">
            <Sparkles className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
            Categorización automática con IA
          </Badge>

          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Las finanzas de tu negocio,{" "}
            <span className="bg-gradient-to-r from-primary to-primary/50 bg-clip-text text-transparent">
              en piloto automático
            </span>
          </h1>

          <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
            Registrá tus ingresos y gastos, dejá que la inteligencia
            artificial los clasifique por vos y mirá cómo le va a tu negocio
            en un dashboard siempre actualizado.
          </p>

          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row lg:justify-start">
            <Link
              to="/register"
              className={cn(buttonVariants({ size: "lg" }), "w-full gap-2 sm:w-auto")}
            >
              Comenzar gratis
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <a
              href="#how-it-works"
              className={cn(
                buttonVariants({ variant: "outline", size: "lg" }),
                "w-full gap-2 sm:w-auto",
              )}
            >
              <PlayCircle className="h-4 w-4" aria-hidden="true" />
              Ver cómo funciona
            </a>
          </div>

          <p className="mt-4 text-sm text-muted-foreground">
            Sin tarjeta de crédito · Configuración en minutos
          </p>
        </div>

        <div className="relative mx-auto w-full max-w-md lg:max-w-none">
          <HeroPreviewCard />
        </div>
      </div>
    </section>
  );
}

/** Purely decorative product mockup — not real data, hidden from assistive tech. */
function HeroPreviewCard() {
  const bars = [40, 65, 45, 80, 60, 95, 70];

  return (
    <div aria-hidden="true" className="relative">
      <div className="animate-float rounded-2xl border border-border bg-card p-6 shadow-2xl shadow-primary/10">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Balance de julio</p>
            <p className="text-3xl font-bold text-foreground">$284.500</p>
          </div>
          <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
            +12,4%
          </span>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-muted p-3">
            <p className="text-xs text-muted-foreground">Ingresos</p>
            <p className="text-lg font-semibold text-foreground">$412.000</p>
          </div>
          <div className="rounded-lg bg-muted p-3">
            <p className="text-xs text-muted-foreground">Gastos</p>
            <p className="text-lg font-semibold text-foreground">$127.500</p>
          </div>
        </div>

        <div className="flex h-24 items-end gap-2">
          {bars.map((height, index) => (
            <div
              key={index}
              className="flex-1 rounded-t-sm bg-primary/70"
              style={{ height: `${height}%` }}
            />
          ))}
        </div>
      </div>

      <div className="absolute -bottom-8 -left-8 hidden animate-float rounded-xl border border-border bg-card px-4 py-3 shadow-xl [animation-delay:1s] sm:block">
        <p className="text-xs text-muted-foreground">Categorizado por IA</p>
        <p className="text-sm font-semibold text-foreground">🍔 Alimentos · 96%</p>
      </div>
    </div>
  );
}
