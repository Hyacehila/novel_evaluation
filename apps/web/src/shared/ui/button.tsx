import Link from "next/link";
import type { ComponentProps } from "react";

import { cn } from "@/shared/lib/cn";


const baseClasses =
  "inline-flex items-center justify-center rounded-full border px-4 py-2 text-sm font-medium transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60";

const variants = {
  primary:
    "border-transparent bg-[var(--accent)] text-white shadow-[0_14px_30px_rgba(180,70,42,0.24)] hover:bg-[var(--accent-strong)]",
  secondary:
    "border-[var(--line-strong)] bg-[var(--surface-strong)] text-[var(--foreground)] hover:border-[var(--accent)] hover:text-[var(--accent-strong)]",
  ghost:
    "border-transparent bg-transparent text-[var(--muted)] hover:border-[var(--line)] hover:bg-white/60 hover:text-[var(--foreground)]",
};

type ButtonVariant = keyof typeof variants;

type BaseProps = {
  className?: string;
  variant?: ButtonVariant;
};

type LinkProps = BaseProps & {
  asLink: true;
  href: string;
  prefetch?: ComponentProps<typeof Link>["prefetch"];
  children: ComponentProps<typeof Link>["children"];
};

type NativeButtonProps = BaseProps &
  ComponentProps<"button"> & {
    asLink?: false;
  };

export function Button(props: LinkProps | NativeButtonProps) {
  const className = cn(baseClasses, variants[props.variant ?? "primary"], props.className);

  if (props.asLink) {
    return (
      <Link href={props.href} prefetch={props.prefetch} className={className}>
        {props.children}
      </Link>
    );
  }

  const { asLink: _asLink, className: _className, variant, ...buttonProps } = props;
  void _asLink;
  void _className;
  void variant;

  return <button {...buttonProps} className={className} />;
}
