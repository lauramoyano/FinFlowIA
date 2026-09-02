import { useTranslation } from "react-i18next";
import { Reveal } from "@/shared/components/Reveal";
import { STEPS } from "@/features/landing/data/landing-content";

export function HowItWorksSection() {
  const { t } = useTranslation("landing");

  return (
    <section id="how-it-works" aria-labelledby="how-it-works-heading" className="py-20 sm:py-28">
      <div className="container">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 id="how-it-works-heading" className="text-3xl font-bold tracking-tight sm:text-4xl">
            {t("howItWorks.heading")}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            {t("howItWorks.subtitle")}
          </p>
        </Reveal>

        <div role="list" className="mt-16 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, index) => (
            <Reveal
              key={step.id}
              role="listitem"
              delay={index * 100}
              className="relative flex flex-col items-center text-center lg:items-start lg:text-left"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                {index + 1}
              </div>
              <step.icon className="mb-2 h-5 w-5 text-primary" aria-hidden="true" />
              <h3 className="text-base font-semibold text-foreground">
                {t(`howItWorks.items.${step.id}.title`)}
              </h3>
              <p className="mt-1.5 text-sm text-muted-foreground">
                {t(`howItWorks.items.${step.id}.description`)}
              </p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
