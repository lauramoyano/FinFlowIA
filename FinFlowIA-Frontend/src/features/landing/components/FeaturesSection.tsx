import { useTranslation } from "react-i18next";
import { Reveal } from "@/shared/components/Reveal";
import { Card, CardContent } from "@/shared/components/ui/Card";
import { FEATURES } from "@/features/landing/data/landing-content";

export function FeaturesSection() {
  const { t } = useTranslation("landing");

  return (
    <section
      id="features"
      aria-labelledby="features-heading"
      className="border-t border-border bg-muted/30 py-20 sm:py-28"
    >
      <div className="container">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 id="features-heading" className="text-3xl font-bold tracking-tight sm:text-4xl">
            {t("features.heading")}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            {t("features.subtitle")}
          </p>
        </Reveal>

        <div role="list" className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature, index) => (
            <Reveal key={feature.id} role="listitem" delay={index * 75}>
              <Card className="h-full border-border/60 transition-shadow hover:shadow-lg">
                <CardContent className="p-6">
                  <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <feature.icon className="h-6 w-6" aria-hidden="true" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {t(`features.items.${feature.id}.title`)}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {t(`features.items.${feature.id}.description`)}
                  </p>
                </CardContent>
              </Card>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
