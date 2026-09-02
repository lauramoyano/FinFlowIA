import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Reveal } from "@/shared/components/Reveal";
import { buttonVariants } from "@/shared/components/ui/Button";
import { cn } from "@/shared/lib/utils";

export function CTASection() {
  const { t } = useTranslation("landing");

  return (
    <section className="py-20 sm:py-28">
      <div className="container">
        <Reveal className="relative overflow-hidden rounded-3xl bg-primary px-6 py-16 text-center sm:px-16">
          <div aria-hidden="true" className="pointer-events-none absolute inset-0">
            <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
            <div className="absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
          </div>
          <h2 className="relative text-3xl font-bold tracking-tight text-primary-foreground sm:text-4xl">
            {t("cta.heading")}
          </h2>
          <p className="relative mx-auto mt-4 max-w-xl text-lg text-primary-foreground/80">
            {t("cta.subtitle")}
          </p>
          <Link
            to="/register"
            className={cn(
              buttonVariants({ variant: "secondary", size: "lg" }),
              "relative mt-8 gap-2 bg-white text-primary hover:bg-white/90",
            )}
          >
            {t("cta.button")}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}
