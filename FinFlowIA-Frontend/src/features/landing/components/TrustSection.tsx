import { Reveal } from "@/shared/components/Reveal";
import { TRUST_INDICATORS } from "@/features/landing/data/landing-content";

export function TrustSection() {
  return (
    <section aria-labelledby="trust-heading" className="border-y border-border py-14">
      <div className="container">
        <h2 id="trust-heading" className="sr-only">
          Por qué confiar en FinFlowIA
        </h2>
        <div role="list" className="grid gap-8 sm:grid-cols-3">
          {TRUST_INDICATORS.map((item, index) => (
            <Reveal
              key={item.title}
              role="listitem"
              delay={index * 75}
              className="flex items-start gap-4"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                <item.icon className="h-5 w-5" aria-hidden="true" />
              </div>
              <div>
                <p className="font-semibold text-foreground">{item.title}</p>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
