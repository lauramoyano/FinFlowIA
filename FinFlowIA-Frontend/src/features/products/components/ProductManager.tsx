import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import { Pencil, Trash2 } from "lucide-react";
import {
  useCreateProduct,
  useDeleteProduct,
  useProducts,
  useUpdateProduct,
} from "@/features/products/hooks/useProducts";
import {
  createProductSchema,
  type CreateProductFormValues,
} from "@/features/products/schemas/product.schema";
import type { Product } from "@/features/products/types/product.types";
import { formatCurrency } from "@/shared/lib/utils";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import { LoadingSpinner } from "@/shared/components/LoadingSpinner";

interface EditFormValues {
  name: string;
  unit_label: string;
  unit_insumos_cost: string;
  unit_sale_price: string;
}

// A div-based "row" instead of a literal <table> — lets each row collapse
// into a stacked card on narrow screens instead of squeezing columns (or
// clipping the action buttons) the way a table would.
function ProductRow({
  product,
  onDelete,
  isDeleting,
}: {
  product: Product;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}) {
  const { t } = useTranslation("products");
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState<EditFormValues>({
    name: product.name,
    unit_label: product.unit_label ?? "",
    unit_insumos_cost: product.unit_insumos_cost,
    unit_sale_price: product.unit_sale_price ?? "",
  });
  const updateMutation = useUpdateProduct();

  const startEditing = () => {
    setForm({
      name: product.name,
      unit_label: product.unit_label ?? "",
      unit_insumos_cost: product.unit_insumos_cost,
      unit_sale_price: product.unit_sale_price ?? "",
    });
    setIsEditing(true);
  };

  const save = () => {
    updateMutation.mutate(
      {
        id: product.id,
        data: {
          name: form.name,
          unit_label: form.unit_label || undefined,
          unit_insumos_cost: form.unit_insumos_cost,
          unit_sale_price: form.unit_sale_price || undefined,
        },
      },
      { onSuccess: () => setIsEditing(false) },
    );
  };

  if (isEditing) {
    return (
      <div className="space-y-3 py-3" data-testid="product-row">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <Input
            label={t("form.nameLabel")}
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          <Input
            label={t("form.unitLabelLabel")}
            value={form.unit_label}
            onChange={(e) => setForm((f) => ({ ...f, unit_label: e.target.value }))}
          />
          <Input
            label={t("form.costLabel")}
            type="number"
            step="0.01"
            min="0"
            value={form.unit_insumos_cost}
            onChange={(e) => setForm((f) => ({ ...f, unit_insumos_cost: e.target.value }))}
            data-testid="product-cost-input"
          />
          <Input
            label={t("form.salePriceLabel")}
            type="number"
            step="0.01"
            min="0"
            value={form.unit_sale_price}
            onChange={(e) => setForm((f) => ({ ...f, unit_sale_price: e.target.value }))}
            data-testid="product-sale-price-input"
          />
        </div>
        <div className="flex gap-2">
          <Button size="sm" onClick={save} isLoading={updateMutation.isPending} data-testid="product-save">
            {t("list.save")}
          </Button>
          <Button size="sm" variant="outline" onClick={() => setIsEditing(false)}>
            {t("list.cancel")}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:gap-4"
      data-testid="product-row"
    >
      <div className="min-w-0 sm:w-40 sm:shrink-0">
        <p className="truncate text-sm font-medium">
          {product.name}
          {product.unit_label && (
            <span className="ml-1 font-normal text-xs text-muted-foreground">
              ({product.unit_label})
            </span>
          )}
        </p>
      </div>

      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm sm:flex-1">
        <div className="flex items-baseline gap-1.5">
          <span className="text-xs text-muted-foreground">{t("list.columns.cost")}:</span>
          <span>{formatCurrency(product.unit_insumos_cost)}</span>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="text-xs text-muted-foreground">{t("list.columns.salePrice")}:</span>
          {product.unit_sale_price ? (
            <span>{formatCurrency(product.unit_sale_price)}</span>
          ) : (
            <span className="text-muted-foreground">{t("list.noPrice")}</span>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={startEditing}
          className="h-7 gap-1 px-2.5 text-xs"
          data-testid="product-edit"
        >
          <Pencil className="h-3.5 w-3.5" />
          {t("list.edit")}
        </Button>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => onDelete(product.id)}
          disabled={isDeleting}
          className="h-7 gap-1 border-destructive/30 px-2.5 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive"
        >
          <Trash2 className="h-3.5 w-3.5" />
          {t("list.delete")}
        </Button>
      </div>
    </div>
  );
}

export function ProductManager() {
  const { t } = useTranslation("products");
  const { data: products = [], isLoading } = useProducts();
  const createMutation = useCreateProduct();
  const deleteMutation = useDeleteProduct();

  const productSchema = useMemo(() => createProductSchema(t), [t]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateProductFormValues>({
    resolver: zodResolver(productSchema),
  });

  const onSubmit = (data: CreateProductFormValues) => {
    createMutation.mutate(
      {
        name: data.name,
        unit_label: data.unit_label || undefined,
        unit_insumos_cost: data.unit_insumos_cost,
        unit_sale_price: data.unit_sale_price,
      },
      { onSuccess: () => reset() },
    );
  };

  return (
    <div className="rounded-lg border bg-card p-4 sm:p-6" data-testid="product-manager">
      {isLoading ? (
        <div className="flex h-24 items-center justify-center">
          <LoadingSpinner size="sm" />
        </div>
      ) : products.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("list.empty")}</p>
      ) : (
        <div className="divide-y">
          {products.map((product) => (
            <ProductRow
              key={product.id}
              product={product}
              onDelete={(id) => deleteMutation.mutate(id)}
              isDeleting={deleteMutation.isPending}
            />
          ))}
        </div>
      )}

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mt-6 grid grid-cols-1 gap-3 border-t pt-4 sm:grid-cols-2 lg:flex lg:flex-wrap lg:items-end"
      >
        <Input
          label={t("form.nameLabel")}
          placeholder={t("form.namePlaceholder")}
          error={errors.name?.message}
          {...register("name")}
        />
        <Input
          label={t("form.unitLabelLabel")}
          placeholder={t("form.unitLabelPlaceholder")}
          error={errors.unit_label?.message}
          {...register("unit_label")}
        />
        <Input
          label={t("form.costLabel")}
          type="number"
          step="0.01"
          min="0"
          error={errors.unit_insumos_cost?.message}
          {...register("unit_insumos_cost")}
        />
        <Input
          label={t("form.salePriceLabel")}
          type="number"
          step="0.01"
          min="0"
          error={errors.unit_sale_price?.message}
          {...register("unit_sale_price")}
        />

        <Button type="submit" isLoading={createMutation.isPending} className="sm:col-span-2 lg:col-auto">
          {t("form.submit")}
        </Button>
      </form>

      {createMutation.isError && (
        <p className="mt-2 text-sm text-destructive">{t("form.createError")}</p>
      )}
    </div>
  );
}
