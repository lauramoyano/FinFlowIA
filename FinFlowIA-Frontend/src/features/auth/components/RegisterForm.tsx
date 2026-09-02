import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useRegister } from "@/features/auth/hooks/useAuth";
import {
  createRegisterSchema,
  type RegisterFormValues,
} from "@/features/auth/schemas/auth.schema";
import { Button } from "@/shared/components/ui/Button";
import { Input } from "@/shared/components/ui/Input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/Card";

export function RegisterForm() {
  const registerMutation = useRegister();
  const { t } = useTranslation("auth");
  const registerSchema = useMemo(() => createRegisterSchema(t), [t]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = ({ confirmPassword: _, ...data }: RegisterFormValues) => {
    registerMutation.mutate(data);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl">{t("register.title")}</CardTitle>
        <CardDescription>{t("register.subtitle")}</CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {registerMutation.isError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {t("register.failed")}
            </div>
          )}

          {registerMutation.isSuccess && (
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-950/40 dark:text-green-400">
              {t("register.success")}
            </div>
          )}

          <Input
            label={t("register.fullNameLabel")}
            type="text"
            placeholder={t("register.fullNamePlaceholder")}
            error={errors.full_name?.message}
            {...register("full_name")}
          />

          <Input
            label={t("register.emailLabel")}
            type="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register("email")}
          />

          <Input
            label={t("register.passwordLabel")}
            type="password"
            placeholder={t("register.passwordPlaceholder")}
            error={errors.password?.message}
            {...register("password")}
          />

          <Input
            label={t("register.confirmPasswordLabel")}
            type="password"
            placeholder={t("register.confirmPasswordPlaceholder")}
            error={errors.confirmPassword?.message}
            {...register("confirmPassword")}
          />
        </CardContent>

        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            isLoading={registerMutation.isPending}
          >
            {t("register.submit")}
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            {t("register.haveAccount")}{" "}
            <Link
              to="/login"
              className="text-primary underline-offset-4 hover:underline"
            >
              {t("register.signIn")}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
