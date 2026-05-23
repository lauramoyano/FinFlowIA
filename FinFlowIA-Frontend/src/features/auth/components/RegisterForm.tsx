import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "react-router-dom";
import { useRegister } from "@/features/auth/hooks/useAuth";
import {
  registerSchema,
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
        <CardTitle className="text-2xl">Create an account</CardTitle>
        <CardDescription>
          Start managing your business finances with AI
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          {registerMutation.isError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              Registration failed. The email may already be in use.
            </div>
          )}

          {registerMutation.isSuccess && (
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-700">
              Account created! You can now sign in.
            </div>
          )}

          <Input
            label="Full Name"
            type="text"
            placeholder="Jane Doe"
            error={errors.full_name?.message}
            {...register("full_name")}
          />

          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register("email")}
          />

          <Input
            label="Password"
            type="password"
            placeholder="Minimum 8 characters"
            error={errors.password?.message}
            {...register("password")}
          />

          <Input
            label="Confirm Password"
            type="password"
            placeholder="Repeat your password"
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
            Create Account
          </Button>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-primary underline-offset-4 hover:underline"
            >
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
