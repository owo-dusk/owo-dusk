# Contributing Guidelines

Hey there, thanks for wanting to contribute! OwO-Dusk is an open source and free project, and we welcome any PR.

---

## How to Contribute

### 1. Fork & Clone
Fork the repo on GitHub, then clone your fork locally:
```
git clone https://github.com/YOUR_USERNAME/owo-dusk.git
cd owo-dusk
```

### 2. Add Upstream Remote
```
git remote add upstream https://github.com/owo-dusk/owo-dusk.git
git fetch upstream
```

### 3. Create a Branch
Branch off from `beta` if possible, `main` for bug fixes:
```
git checkout -b my-feature upstream/beta
```

### 4. Make Your Changes
Run the bot locally to test before submitting.

### 5. Commit & Push
```
git add .
git commit -m "feat: describe your change"
git push origin my-feature
```

### 6. Open a Pull Request
Open a PR on GitHub targeting the `beta` branch (or `main` for bug fixes) and describe what you changed and why.

---

## Guidelines

1) Keep one Pull Request(PR) per feature. Don't put everything into one PR.
2) For major changes, please contact me on Discord - @echoquill
3) For commit messages, use prefixes like `feat`, `chore`, `refactor`, `fix` etc. as required

I would also appreciate it if you check whether the `beta` branch is more up to date than `main` and make the PR there instead. This is not required but will help a lot!
(For bug fixes, feel free to use the `main` branch!)

Thanks again :>