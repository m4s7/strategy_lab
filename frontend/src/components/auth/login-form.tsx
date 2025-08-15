"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Checkbox } from "@/components/ui/checkbox";
import { useAuth } from "@/lib/auth/auth-provider";
import {
  useAuditLog,
  SecurityEvents,
  assessRisk,
} from "@/lib/security/audit-logger";
import { usePasswordStrength } from "@/lib/security/encryption";
import { Shield, AlertCircle, Lock, User, Key } from "lucide-react";
import { Progress } from "@/components/ui/progress";

export function LoginForm() {
  const router = useRouter();
  const { login } = useAuth();
  const { logAction } = useAuditLog();
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    mfaCode: "",
    rememberMe: false,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showMfa, setShowMfa] = useState(false);
  const [failedAttempts, setFailedAttempts] = useState(0);

  const passwordStrength = usePasswordStrength(formData.password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Log login attempt
      await logAction(SecurityEvents.LOGIN_ATTEMPT, "auth/login", "success", {
        username: formData.username,
      });

      await login({
        username: formData.username,
        password: formData.password,
        mfaCode: formData.mfaCode,
      });

      // Log successful login
      await logAction(SecurityEvents.LOGIN_SUCCESS, "auth/login", "success", {
        username: formData.username,
      });

      // Redirect to dashboard
      router.push("/dashboard");
    } catch (error: any) {
      const newFailedAttempts = failedAttempts + 1;
      setFailedAttempts(newFailedAttempts);

      // Log failed login
      await logAction(
        SecurityEvents.LOGIN_FAILURE,
        "auth/login",
        "failure",
        {
          username: formData.username,
          error: error.message,
          failedAttempts: newFailedAttempts,
        },
        assessRisk(SecurityEvents.LOGIN_FAILURE, {
          failedAttempts: newFailedAttempts,
        })
      );

      if (error.code === "MFA_REQUIRED") {
        setShowMfa(true);
      } else {
        setError(
          error.message || "Login failed. Please check your credentials."
        );
      }

      // Lock account after too many attempts
      if (newFailedAttempts >= 5) {
        setError(
          "Account locked due to multiple failed attempts. Please contact support."
        );
        await logAction(
          SecurityEvents.SUSPICIOUS_ACTIVITY,
          "auth/login",
          "failure",
          {
            username: formData.username,
            reason: "Multiple failed login attempts",
            failedAttempts: newFailedAttempts,
          },
          "critical"
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <Shield className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-2xl text-center">Secure Login</CardTitle>
          <CardDescription className="text-center">
            Enter your credentials to access Strategy Lab
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="username"
                  type="text"
                  placeholder="Enter your username"
                  value={formData.username}
                  onChange={(e) =>
                    setFormData({ ...formData, username: e.target.value })
                  }
                  className="pl-10"
                  required
                  disabled={loading || failedAttempts >= 5}
                  autoComplete="username"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  className="pl-10"
                  required
                  disabled={loading || failedAttempts >= 5}
                  autoComplete="current-password"
                />
              </div>
              {formData.password && (
                <div className="space-y-1">
                  <Progress
                    value={passwordStrength.score * 10}
                    className="h-2"
                  />
                  <p className="text-xs text-muted-foreground">
                    Password strength: {passwordStrength.strength}
                  </p>
                </div>
              )}
            </div>

            {showMfa && (
              <div className="space-y-2">
                <Label htmlFor="mfaCode">Two-Factor Code</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="mfaCode"
                    type="text"
                    placeholder="Enter 6-digit code"
                    value={formData.mfaCode}
                    onChange={(e) =>
                      setFormData({ ...formData, mfaCode: e.target.value })
                    }
                    className="pl-10"
                    maxLength={6}
                    pattern="[0-9]{6}"
                    disabled={loading}
                    autoComplete="one-time-code"
                  />
                </div>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <Checkbox
                id="remember"
                checked={formData.rememberMe}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, rememberMe: checked as boolean })
                }
                disabled={loading}
              />
              <Label
                htmlFor="remember"
                className="text-sm font-normal cursor-pointer"
              >
                Remember me for 30 days
              </Label>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full"
              disabled={loading || failedAttempts >= 5}
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
            <div className="text-center text-sm text-muted-foreground">
              <a href="/auth/forgot-password" className="hover:underline">
                Forgot your password?
              </a>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
