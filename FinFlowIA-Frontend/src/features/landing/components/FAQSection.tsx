import { useTranslation } from "react-i18next";
import { Reveal } from "@/shared/components/Reveal";
import { Accordion, AccordionItem } from "@/shared/components/ui/Accordion";
import { FAQ_IDS } from "@/features/landing/data/landing-content";

export function FAQSection() {
  const { t } = useTranslation("landing");

  return (
    <section id="faq" aria-labelledby="faq-heading" className="border-t border-border py-20 sm:py-28">
      <div className="container max-w-3xl">
        <Reveal className="text-center">
          <h2 id="faq-heading" className="text-3xl font-bold tracking-tight sm:text-4xl">
            {t("faq.heading")}
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            {t("faq.subtitle")}
          </p>
        </Reveal>

        <Reveal delay={100} className="mt-12">
          <Accordion defaultValue={FAQ_IDS[0]}>
            {FAQ_IDS.map((id) => (
              <AccordionItem key={id} value={id} question={t(`faq.items.${id}.question`)}>
                {t(`faq.items.${id}.answer`)}
              </AccordionItem>
            ))}
          </Accordion>
        </Reveal>
      </div>
    </section>
  );
}
