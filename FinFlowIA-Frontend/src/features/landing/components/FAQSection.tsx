import { Reveal } from "@/shared/components/Reveal";
import { Accordion, AccordionItem } from "@/shared/components/ui/Accordion";
import { FAQ_ITEMS } from "@/features/landing/data/landing-content";

export function FAQSection() {
  return (
    <section id="faq" aria-labelledby="faq-heading" className="border-t border-border py-20 sm:py-28">
      <div className="container max-w-3xl">
        <Reveal className="text-center">
          <h2 id="faq-heading" className="text-3xl font-bold tracking-tight sm:text-4xl">
            Preguntas frecuentes
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            ¿No encontrás lo que buscás? Escribinos y te respondemos.
          </p>
        </Reveal>

        <Reveal delay={100} className="mt-12">
          <Accordion defaultValue={FAQ_ITEMS[0]?.question}>
            {FAQ_ITEMS.map((item) => (
              <AccordionItem key={item.question} value={item.question} question={item.question}>
                {item.answer}
              </AccordionItem>
            ))}
          </Accordion>
        </Reveal>
      </div>
    </section>
  );
}
