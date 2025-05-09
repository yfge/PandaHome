"use client"

import { MainNav } from "./main-nav"
import { UserNav } from "./user-nav"
import { LanguageSwitcher } from "../language-switcher"

export function Header() {
  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4">
        <MainNav />
        <div className="ml-auto flex items-center space-x-4">
          <LanguageSwitcher />
          <UserNav />
        </div>
      </div>
    </div>
  )
} 