
# Verdade ou Fake (Fact Checking API)

API simples em FastAPI para consultar a API externa de checagem de fatos (Google Fact Check Tools API) com **fallback automático para um modelo de ML treinado localmente** quando o serviço externo estiver indisponível.

## Requisitos

- Python 3.14+
- Uma chave de API configurada em `API_KEY` (opcional — sem ela, o modelo local é usado diretamente)

## Como executar

1) (Opcional) Configure a variável de ambiente:

```bash
export API_KEY="SUA_CHAVE_AQUI"
```

2) Instale as dependências e execute o app:

```bash
uv sync
.venv/bin/python main.py
```

A API sobe por padrão em `http://localhost:8000`.

## Endpoint

### Buscar claims

`GET /fact-check/claims/search`

Parâmetros de consulta:

- `query` (string, obrigatório): texto da consulta

Observações importantes:

- A requisição **não possui body** (o body deve ser vazio).
- A `API_KEY` é enviada em toda chamada externa como query param `key`.
- Quando a API externa falha ou não encontra resultados, o endpoint automaticamente utiliza um **modelo SVM treinado** como fallback e indica `"fallback": true` na resposta.

### Exemplos de chamada (curl)

Use `-G` com `--data-urlencode` para consultas com espaços e acentos. O `jq` é opcional — formata a saída para leitura humana.

#### 1. Afirmação verdadeira (modelo local como fallback)

```bash
curl -sS -G "http://localhost:8000/fact-check/claims/search" \
  --data-urlencode "query=A urna eletrônica é usada no Brasil desde 1996" \
  | jq
```

<details>
<summary>Resposta</summary>

```json
{
  "claims": [
    {
      "claim": "A urna eletrônica é usada no Brasil desde 1996",
      "resultado": "Verdadeiro",
      "confianca_verdadeiro": 0.967,
      "confianca_falso": 0.033,
      "threshold": 0.45,
      "fonte": "modelo_local"
    }
  ],
  "nextPageToken": "",
  "fallback": true
}
```

</details>

#### 2. Fake news (resultados da API Google)

```bash
curl -sS -G "http://localhost:8000/fact-check/claims/search" \
  --data-urlencode "query=urnas eletrônicas fraude" \
  | jq
```

<details>
<summary>Resposta (resumida)</summary>

```json
{
  "claims": [
    {
      "text": "TSE destruiu 200 mil urnas para apagar rastros de fraude...",
      "claimant": "Boato nas redes sociais",
      "claimReview": [
        {
          "publisher": { "name": "Estadão", "site": "estadao.com.br" },
          "title": "Descarte de urnas eletrônicas antigas não apaga dados...",
          "textualRating": "Enganoso",
          "languageCode": "pt"
        }
      ]
    }
  ],
  "nextPageToken": "",
  "fallback": false
}
```

</details>

#### 3. Afirmação falsa (modelo local como fallback)

```bash
curl -sS -G "http://localhost:8000/fact-check/claims/search" \
  --data-urlencode "query=Chips chineses foram encontrados nas urnas eletrônicas" \
  | jq
```

<details>
<summary>Resposta</summary>

```json
{
  "claims": [
    {
      "claim": "Chips chineses foram encontrados nas urnas eletrônicas",
      "resultado": "Falso",
      "confianca_verdadeiro": 0.067,
      "confianca_falso": 0.933,
      "threshold": 0.45,
      "fonte": "modelo_local"
    }
  ],
  "nextPageToken": "",
  "fallback": true
}
```

</details>

#### 4. Consulta com vários termos (sem `jq`, saída bruta)

```bash
curl -sS -G "http://localhost:8000/fact-check/claims/search" \
  --data-urlencode "query=vacina covid efeitos colaterais"
```

#### 5. Erro: query ausente

```bash
curl -sS "http://localhost:8000/fact-check/claims/search" | jq
```

Resposta:

```json
{
  "detail": {
    "mensagem": "O parâmetro 'query' é obrigatório."
  }
}
```

---

### Formato da resposta (API Google)

Quando a consulta é atendida pela API externa (`"fallback": false`):

```json
{
  "claims": [
    {
      "text": "...",
      "claimant": "...",
      "claimDate": "2024-01-01T00:00:00Z",
      "claimReview": [
        {
          "publisher": {
            "name": "...",
            "site": "..."
          },
          "url": "...",
          "title": "...",
          "textualRating": "...",
          "languageCode": "pt"
        }
      ]
    }
  ],
  "nextPageToken": "",
  "fallback": false
}
```

### Formato da resposta (modelo local)

Quando o modelo de ML é usado como fallback (`"fallback": true`):

```json
{
  "claims": [
    {
      "claim": "texto da consulta",
      "resultado": "Verdadeiro",
      "confianca_verdadeiro": 0.8286,
      "confianca_falso": 0.1714,
      "threshold": 0.45,
      "fonte": "modelo_local"
    }
  ],
  "nextPageToken": "",
  "fallback": true
}
```

Notas sobre o schema:

- `claims` é uma lista; cada item pode conter campos adicionais retornados pelo serviço externo.
- `nextPageToken` pode vir vazio quando não há mais páginas.
- `fallback` indica se o resultado veio do modelo local (`true`) ou da API Google (`false`).
- O modelo local (`fonte: "modelo_local"`) é um SVM Linear com vetorização TF-IDF word+char n-grams, treinado com ~200 afirmações políticas brasileiras (acurácia 97.6%).

## Erros (pt-BR, sanitizados)

Todos os erros são retornados com `detail.mensagem` em português-br e sem informações sensíveis.

### Query ausente ou vazia

HTTP `400`:

```json
{
  "detail": {
    "mensagem": "O parâmetro 'query' é obrigatório."
  }
}
```

### Nenhum resultado encontrado (claims vazio)

HTTP `404`:

```json
{
  "detail": {
    "mensagem": "Nenhum resultado encontrado para a consulta informada."
  }
}
```

### Falhas ao consultar o serviço externo

Exemplos:

- Timeout: HTTP `504`
- Falha de conexão: HTTP `503`
- Serviço externo indisponível / erro inesperado: HTTP `502`

Formato:

```json
{
  "detail": {
    "mensagem": "Tempo limite ao consultar o serviço externo."
  }
}
```

> **Nota sobre fallback:** Os erros de serviço externo (503, 504, 502) são capturados internamente e o endpoint automaticamente utiliza o modelo local. O cliente **não** recebe esses erros quando o fallback é bem-sucedido — a resposta é HTTP `200` com `"fallback": true`.

