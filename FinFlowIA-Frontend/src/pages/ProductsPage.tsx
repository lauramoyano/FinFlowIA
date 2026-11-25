import { useTranslation } from "react-i18next";
import { ProductManager } from "@/features/products/components/ProductManager";

export function ProductsPage() {
  const { t } = useTranslation("products");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold" data-testid="page-title">{t("page.title")}</h1>
        <p className="text-muted-foreground">{t("page.subtitle")}</p>
      </div>

      <ProductManager />
    </div>
  );
}
