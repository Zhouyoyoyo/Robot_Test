# Robot_Test Framework Architecture

## Core Principles

- Page objects contain NO selenium logic
- All technical capabilities live in Mixins
- Driver lifecycle is managed centrally
- Screenshots are controlled by pytest hooks
- Mailer is decoupled from execution logic

## Forbidden Patterns

- webdriver.Chrome() in test/page
- time.sleep() without warning
- screenshot inside Page
- duplicated BasePage
