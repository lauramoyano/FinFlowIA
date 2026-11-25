import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useLogin } from "@/features/auth/hooks/useAuth";
import {
  createLoginSchema,
  type LoginFormValues,
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

export function LoginForm() {
  const loginMutation = useLogin();
  const { t } = useTranslation("auth");
  const loginSchema = useMemo(() => createLoginSchema(t), [t]);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginFormValues) => {
    loginMutation.mutate(data);
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl">{t("login.title")}</CardTitle>
        <CardDescription>{t("login.subtitle")}</CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {loginMutation.isError && (
            <div
              className="rounded-md bg-destructive/10 p-3 text-sm text-destructive"
              data-testid="login-error"
            >
              {t("login.invalidCredentials")}
            </div>
          )}

          <Input
            label={t("login.emailLabel")}
            type="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register("email")}
          />

          <Input
            label={t("login.passwordLabel")}
            type="password"
            placeholder="••••••••"
            error={errors.password?.message}
            {...register("password")}
          />
        </CardContent>

        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            isLoading={loginMutation.isPending}
          >
            {t("login.submit")}
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            {t("login.noAccount")}{" "}
            <Link
              to="/register"
              className="text-primary underline-offset-4 hover:underline"
            >
              {t("login.signUp")}
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
