import { useTranslation } from "react-i18next";
import { TransactionChatInput } from "@/features/transactions/components/TransactionChatInput";

export function HomePage() {
  const { t } = useTranslation("nav");
  const { t: tTransactions } = useTranslation("transactions");

  return (
    <div className="mx-auto flex h-[calc(100vh-7rem)] max-w-3xl flex-col">
      <div className="pb-4">
        <h1 className="text-2xl font-bold" data-testid="page-title">{t("home")}</h1>
        <p className="text-muted-foreground">{tTransactions("chat.homeSubtitle")}</p>
      </div>

      <TransactionChatInput persistKey="home" heightClassName="flex-1" />
    </div>
  );
}
