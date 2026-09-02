import { useTranslation } from "react-i18next";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

export function RegisterPage() {
  const { t } = useTranslation("auth");

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground text-xl font-bold">
            FF
          </div>
          <h1 className="text-3xl font-bold">FinFlowIA</h1>
          <p className="mt-1 text-muted-foreground">
            {t("register.pageSubtitle")}
          </p>
        </div>
        <RegisterForm />
      </div>
    </div>
  );
}
