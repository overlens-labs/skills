---
name: auto-gitignore
description: Gera, atualiza, recria ou refaz o(s) `.gitignore` de um projeto detectando as tecnologias da codebase (Next.js, Django, Rails, Python, Node, Go, Rust, Terraform, etc.) e baixando templates do gitignore.io. Use SEMPRE que o usuário pedir para criar, gerar, atualizar, configurar, refazer, consertar ou popular o .gitignore — inclusive quando ele NÃO disser "gitignore" mas o contexto for claramente tornar o repo limpo (ex. "tem 200 arquivos não-rastreados no git status", "preciso ignorar os artefatos de build", "node_modules e venv aparecendo no git", "adiciona entradas pro Vercel/Sentry"). Dispara também com `/auto-gitignore`. Reconhece monorepos (Turborepo, Nx, pnpm/yarn workspaces) e gera `.gitignore` por pacote quando faz sentido. Preserva idempotentemente a seção `## Manual setup` com linhas customizadas em re-runs. NÃO use para edições cirúrgicas de uma linha ("remove a linha X"), perguntas conceituais ("o que essa linha faz?") ou comandos git correlatos (`git rm --cached`).
---

# auto-gitignore

## O que esta skill faz

Olha para a codebase do usuário, descobre quais tecnologias estão em uso (Next.js, Python, Docker, Terraform, etc.), e produz um `.gitignore` montado a partir dos templates oficiais do **gitignore.io** (Toptal), preservando uma seção manual no topo para overrides do usuário.

A skill é **idempotente**: rodar de novo num repo que já tem `.gitignore` gerado pela skill apenas atualiza a parte vinda do gitignore.io, sem duplicar entradas nem destruir customizações do usuário.

## Quando ela dispara

- "Gera/cria/atualiza o .gitignore"
- "Configura o gitignore desse projeto"
- "Esse repo não tem gitignore, resolve aí"
- "Adiciona as ignores do Next/Python/Docker"
- `/auto-gitignore`

Não dispara para edição manual cirúrgica de uma linha específica do `.gitignore` (ex. "remove só a linha do `.env.local`"). Nesse caso, edite direto.

## Saída esperada

- **Repo single-package**: um `.gitignore` na raiz.
- **Monorepo** (detectado por `turbo.json`, `nx.json`, `pnpm-workspace.yaml`, ou um `package.json` raiz com `"workspaces"`): um `.gitignore` na raiz, **mais** um `.gitignore` em cada subpacote (`apps/*` e `packages/*` — ou o que o workspace declarar).
- Arquivos temporários em `.temp/` durante a execução; apague-os no final (o `.temp/**` já é coberto pela seção manual).

## Passo a passo

### 1. Identifique a raiz do projeto e se é monorepo

A skill é chamada a partir do diretório raiz do projeto (ou o usuário aponta um caminho). Determine:

- **É monorepo?** Procure (na raiz):
  - `turbo.json`, `nx.json`, `pnpm-workspace.yaml`, `lerna.json`, `rush.json`
  - `package.json` com a chave `"workspaces"` (npm/yarn workspaces)
  - Pasta `apps/` ou `packages/` com múltiplos subdiretórios contendo `package.json`/`pyproject.toml`/etc.
- **Liste os subpacotes** quando for monorepo. Cada subpacote terá sua própria detecção de tecnologias e seu próprio `.gitignore`.

Se houver ambiguidade (ex: existe `apps/` mas o usuário só quer um único `.gitignore` na raiz), pergunte antes de gerar vários arquivos.

### 2. Detecte as tecnologias

Faça uma varredura **leve** da raiz (e de cada subpacote, no caso de monorepo) procurando sinais. Não leia o repo inteiro — basta inspecionar arquivos de manifesto e a presença de diretórios/arquivos típicos. Use a **tabela de sinais** abaixo como guia (mas não se prenda a ela: se você ver evidência clara de outra tecnologia, inclua).

**Tabela de sinais → nome no gitignore.io**

| Sinal observado | Tecnologia (nome canônico no gitignore.io) |
|---|---|
| `package.json` | `node` |
| `package.json` com dep `next` ou pasta `.next/` | `nextjs` |
| `package.json` com dep `react` (sem next) | `react` |
| `package.json` com dep `vue` | `vue` |
| `package.json` com dep `@angular/core` | `angular` |
| `package.json` com dep `svelte` | `svelte` |
| `package.json` com dep `astro` | `astro` |
| `package.json` com dep `nuxt` | `nuxtjs` |
| `package.json` com dep `remix` ou pasta `.remix/` | `remix` |
| `package.json` com dep `vercel` ou pasta `.vercel/` | `vercel` |
| `turbo.json` | `turbo` |
| `yarn.lock` | `yarn` |
| `pyproject.toml` / `requirements*.txt` / `setup.py` / `*.py` | `python` |
| `manage.py` ou dep `django` | `django` |
| `flask` em deps | `flask` |
| `venv/`, `.venv/`, `pyvenv.cfg` | `venv` |
| `Cargo.toml` | `rust` |
| `go.mod` | `go` |
| `Gemfile` | `ruby` |
| `Gemfile` com `rails` | `rails` |
| `pom.xml` | `maven` |
| `build.gradle*` | `gradle` |
| `*.java` (sem maven/gradle) | `java` |
| `*.kt`, `*.kts` | `kotlin` |
| `composer.json` | `composer` |
| `artisan` (Laravel) | `laravel` |
| `Dockerfile` ou `docker-compose*.yml` | (nenhum — gitignore.io não tem template "docker"; pular) |
| `*.tf`, `terraform.tfstate` | `terraform` |
| `.terragrunt-cache/` ou `terragrunt.hcl` | `terragrunt` |
| `serverless.yml` | `serverless` |
| `Pulumi.yaml` | `pulumi` |
| `*.csproj`, `*.sln` | `visualstudio` |
| `*.cs` | `csharp` |
| `*.swift`, `Package.swift` | `swift` ou `swiftpm` |
| `*.xcodeproj/`, `*.xcworkspace/` | `xcode` |
| `flutter` em `pubspec.yaml` | `flutter` |
| `pubspec.yaml` (Dart puro) | `dart` |
| `.idea/` | `intellij+all` (ou `jetbrains+all`) |
| `.vscode/` | `visualstudiocode` |
| `*.sublime-project` | `sublimetext` |
| `*.lua` | `lua` |
| `*.exs`, `mix.exs` | `elixir` |
| `*.erl`, `rebar.config` | `erlang` |
| `*.hs`, `stack.yaml` | `haskell` |
| `*.ex` (Phoenix) | `phoenix` |
| `*.tex` | `latex` |
| `_config.yml` (Jekyll) | `jekyll` |
| `gatsby-config.*` | `gatsby` |
| `hugo.toml` / `config.toml` na raiz de site Hugo | `hugo` |
| `astro.config.*` | `astro` |
| `.expo/` | (use `reactnative`) |
| Plataforma do usuário (informe sempre) | `macos`, `windows`, `linux` |

**Sempre inclua o SO do usuário**. Use `windows` como padrão neste ambiente (Windows 11). Se houver indício de devcontainer ou múltiplos colaboradores em outros SOs, inclua os três (`windows,macos,linux`).

**Sempre inclua `git`** — pega coisas como `*.orig` de merge.

Se o subpacote é só um `package.json` com biblioteca pura (sem framework), inclua apenas `node` (mais o SO e `git` já cobertos pela raiz, então pode até pular se já estiver na raiz).

### 3. Cruze com a lista oficial do gitignore.io

A API expõe a lista de templates válidos em:

```
https://www.toptal.com/developers/gitignore/api/list
```

Baixe-a uma vez (cacheie em `.temp/gitignore/list.txt`) e filtre as tecnologias detectadas para manter só as que existem na lista. Use **exatamente** o nome canônico que aparece na lista da API (case-sensitive — todos minúsculos lá).

Se você detectou uma tecnologia que **não** está na lista (ex: Docker, Supabase, Prisma), apenas registre na seção manual do `.gitignore` (veja passo 5) — não invente templates.

### 4. Baixe e mescle (caminho preferido: `scripts/build_gitignore.py`)

A skill traz um helper Python (stdlib apenas, sem `pip install`) que faz fetch + merge idempotente em uma única chamada. Antes de usar, **verifique se Python está disponível**:

```bash
python --version    # ou: python3 --version
```

Se o comando retornar uma versão (3.6+), use o script — ele encapsula as regras de marcadores e o User-Agent que o gitignore.io exige (sem User-Agent a API retorna 403):

```bash
python <skill-path>/scripts/build_gitignore.py \
    --techs nextjs,node,windows,git \
    --output ./path/to/.gitignore \
    [--validate]
```

O que o script faz:

- **Arquivo não existe** → cria com `## Manual setup\n\n.temp/**\n\n<bloco gitignore.io>`.
- **Arquivo existe COM marcadores** `# Created by https://www.toptal.com/developers/gitignore/api/...` / `# End of ...` → substitui **apenas** o conteúdo entre os marcadores. Tudo fora preserva byte-a-byte (incluindo a seção `## Manual setup` que o usuário pode ter editado com linhas próprias como `secrets/`).
- **Arquivo existe SEM marcadores** (legado) → anexa o bloco gitignore.io ao final. **Antes** de rodar nesse caso, mostre ao usuário o conteúdo atual e confirme — ofereça mesclar o legado como seção manual no topo se ele preferir.
- `--validate` cruza os techs com a lista oficial e descarta os não suportados (extra request, use quando incerto sobre nomes).

Rode uma vez por arquivo de saída (raiz e cada subpacote do monorepo). O script é a fonte única de verdade da regra de marcadores — não duplique essa lógica em outro lugar.

### 4.b Fallback sem Python (`curl` + edição manual)

Se Python não estiver disponível (e nem fizer sentido pedir pro usuário instalar agora), você mesmo executa o equivalente. Não é difícil — são 3 passos. **Importante**: a API do gitignore.io rejeita requests sem User-Agent (retorna 403), então use `curl` (que manda um por padrão) ou passe um header explícito.

**Passo A — baixe o template combinado:**

```bash
curl -fsSL "https://www.toptal.com/developers/gitignore/api/nextjs,node,windows,git" > .temp/gitignore/block.txt
```

O conteúdo vem entre os marcadores `# Created by https://www.toptal.com/developers/gitignore/api/<techs>` e `# End of https://www.toptal.com/developers/gitignore/api/<techs>` — preserve essas linhas intactas, são elas que tornam re-runs idempotentes.

**Passo B — decida o cenário do arquivo de saída e monte o conteúdo:**

1. **Arquivo não existe** → crie escrevendo, nessa ordem exata:
   ```
   ## Manual setup

   .temp/**

   <conteúdo de .temp/gitignore/block.txt>
   ```

2. **Arquivo existe COM marcadores** `# Created by https://www.toptal.com/developers/gitignore/api/...` e `# End of ...` → leia o arquivo inteiro, identifique as linhas de início e fim do bloco gitignore.io (procure pelos prefixos exatos acima), e **substitua apenas o intervalo entre eles** (inclusive as próprias linhas de marcador) pelo novo bloco baixado no passo A. Tudo fora desse intervalo é do usuário e deve ficar byte-a-byte igual — inclusive uma seção `## Manual setup` com linhas próprias como `secrets/` ou `*.private.key`.

3. **Arquivo existe SEM marcadores** (legado) → pare e mostre o conteúdo atual ao usuário. Pergunte se ele prefere (a) anexar o novo bloco ao final mantendo o legado, (b) mover o legado para dentro de `## Manual setup` no topo e colocar o bloco gitignore.io logo abaixo, ou (c) sobrescrever do zero. Só depois aplique.

**Passo C — escreva o arquivo final** com o ferramental que estiver à mão (Edit, Write, `Set-Content -Encoding utf8` no PowerShell — evite `>` no PowerShell, ele escreve UTF-16 com BOM).

A regra dos marcadores é o coração da idempotência — se você violá-la, re-runs vão duplicar entradas ou apagar customizações do usuário. Quando em dúvida, leia o que o script faz (é simples) e replique a mesma lógica.

### 5. Seção manual e idempotência

O `.gitignore` final tem **dois blocos** sempre nessa ordem, e o `build_gitignore.py` já garante isso:

```gitignore
## Manual setup

.temp/**
# <adicione aqui ignores manuais que sobrevivem entre regenerações>

# Created by https://www.toptal.com/developers/gitignore/api/<techs>
# ... conteúdo do gitignore.io ...
# End of https://www.toptal.com/developers/gitignore/api/<techs>
```

A seção `## Manual setup` deve **sempre** conter `.temp/**` (esse diretório é usado pela própria skill durante a execução). O usuário pode adicionar linhas próprias entre `.temp/**` e o bloco gitignore.io; elas sobrevivem a re-runs.

**Caso `.gitignore` legado (sem marcadores):** o script anexa o novo bloco ao final. Avise o usuário e pergunte se ele quer:
  (a) manter o legado como está + bloco gitignore.io no final (default do script),
  (b) mover o legado para dentro de `## Manual setup` no topo e jogar o bloco gitignore.io logo depois, ou
  (c) sobrescrever do zero.

### 6. Dedup final (remover padrões duplicados)

Cenário comum: o repo já tinha um `.gitignore` legado gerado por uma ferramenta como `create-next-app`, `django-admin startproject`, `cargo new` etc. Esses templates trazem padrões como `/.next/`, `node_modules`, `.vercel` no corpo do arquivo (sem marcadores gitignore.io). Quando a skill detecta "arquivo legado, sem marcadores" e anexa o bloco gitignore.io ao final, esses padrões passam a aparecer **duas vezes** — uma vez no corpo legado, outra dentro do bloco gitignore.io.

**Regra:** o bloco gitignore.io é a fonte autoritativa para padrões de tecnologia. Se um padrão (linha não-comentada, não-vazia) aparece **dentro** do bloco E **fora** dele, a ocorrência de fora é redundante e deve ser removida — a de dentro fica, porque é a versão "gerenciada" que se atualiza em re-runs.

**Quando você usou o script:** dedup é automático ao final do `build_gitignore.py`. Ele imprime `removed N duplicate pattern(s)` na saída — se N > 0, mencione isso no resumo. Para desativar (raríssimo), passe `--no-dedupe`.

**Quando você está no fallback sem Python:** faça o dedup à mão depois do passo 4.b. Pseudocódigo:

1. Identifique o bloco gitignore.io pelos marcadores `# Created by .../api/...` / `# End of .../api/...`.
2. Colete os padrões **dentro** do bloco (linhas que não começam com `#` e não são vazias, comparadas pela string trimmed).
3. Percorra as linhas **fora** do bloco. Para cada linha-padrão (não-comentário, não-vazia) cuja string trimmed coincida com algo do conjunto colete em (2), **remova essa linha**.
4. Colapse runs de 3+ linhas em branco em 2 (limpeza cosmética após a remoção).
5. Não remova comentários nem linhas dentro do bloco. Headers órfãos (`# next.js` sem padrões abaixo) podem ficar — são cosméticos.

**Cuidado com comparação:** use match exato da string trimmed. NÃO normalize `/.next/` para `.next/` (rooted vs anywhere é semanticamente diferente em monorepos). Conservadorismo aqui é melhor que esperteza.

### 7. Limpe `.temp/`

Após escrever os arquivos finais, apague `.temp/codebase/` e `.temp/gitignore/`. Como `.temp/**` já está no `.gitignore`, é apenas higiene.

### 8. Resumo para o usuário

Reporte de forma curta:
- Quais tecnologias foram detectadas (e quais foram descartadas por não terem template no gitignore.io).
- Quantos arquivos `.gitignore` foram gerados/atualizados e em quais caminhos.
- Se algum arquivo existente foi mesclado em vez de regenerado do zero.

## Detalhes importantes

### Por que essa estrutura "manual + gerado"?

A API do gitignore.io pode mudar entradas entre versões (raramente, mas acontece), e o usuário inevitavelmente quer adicionar ignores específicos (segredos, pastas locais, artefatos de scripts internos). Separar em dois blocos com marcadores claros deixa óbvio o que é regenerável e o que é responsabilidade do usuário — e permite re-rodar a skill sem medo.

### Por que cachear `list.txt`?

A lista tem ~700 entradas e raramente muda. Cachear evita uma chamada a mais e torna o passo de validação de nomes instantâneo. Não é estritamente necessário, mas se a skill rodar em sequência (monorepo grande), economiza tempo.

### Por que combinar todas as techs em uma única chamada?

A API suporta `tech1,tech2,...` em uma URL só e devolve um único bloco coeso, sem duplicar entradas comuns (ex: `node_modules` aparece em `node` e `nextjs`, mas a API dedup). Múltiplas chamadas separadas produziriam blocos repetidos.

### Como decidir entre `react`, `nextjs`, `remix`?

Use o framework mais específico. Se o `package.json` tem `next`, use `nextjs` (e **não** adicione `react` separado — o template do Next já cobre). Mesma lógica para Remix/Nuxt/Astro.

### Monorepos: o que vai onde?

- **Raiz**: SO + `git` + ferramentas globais do monorepo (`turbo`, `node`, `yarn`/`pnpm`, IDE).
- **Cada `apps/*`**: stack daquele app (ex: `nextjs` para `apps/web`).
- **Cada `packages/*`**: stack daquele pacote (geralmente só `node` para libs TypeScript puras — mas o `node` na raiz já cobre, então pode pular se o subpacote não tem nada específico).

Se um subpacote não traz **nenhuma** tecnologia além das já cobertas pela raiz, **não crie** um `.gitignore` lá. Arquivos vazios são ruído.

### O usuário pediu `.gitignore` mas o repo não é Git ainda

Avise (`git init` provavelmente faz sentido) mas gere o `.gitignore` mesmo assim — é inofensivo.

## Exemplo (mini)

Repo `my-app/` com `package.json` tendo `"next": "14.x"` e nenhum monorepo:

```bash
python <skill>/scripts/build_gitignore.py --techs nextjs,node,windows,git --output ./.gitignore
```

Reporta: "Gerado `.gitignore` (4 técs: nextjs, node, windows, git)."

Repo monorepo `mono/` com `turbo.json`, `apps/web` (Next), `apps/api` (Node puro), `packages/ui` (lib React):

```bash
python <skill>/scripts/build_gitignore.py --techs turbo,node,windows,git --output ./.gitignore
python <skill>/scripts/build_gitignore.py --techs nextjs            --output ./apps/web/.gitignore
python <skill>/scripts/build_gitignore.py --techs react             --output ./packages/ui/.gitignore
# apps/api: nada específico além de Node — NÃO crie .gitignore lá (já coberto pela raiz)
```

Reporta: "Gerados 3 `.gitignore`: `./`, `apps/web/`, `packages/ui/`."
