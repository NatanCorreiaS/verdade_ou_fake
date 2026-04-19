
# Verdade ou Fake (Fact Checking API)

API simples em FastAPI para consultar a API externa de checagem de fatos (Google Fact Check Tools API).

## Requisitos

- Python 3.14+
- Uma chave de API configurada em `API_KEY`

## Como executar

1) Configure a variável de ambiente:

```bash
export API_KEY="SUA_CHAVE_AQUI"
```

2) Execute o app:

```bash
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

#### Exemplo de requisição (representação JSON)

Mesmo sendo um `GET` com query string, a estrutura lógica do request é:

```json
{
	"query": "vacina"
}
```

#### Exemplo de chamada (curl)

```bash
curl -sS "http://localhost:8000/fact-check/claims/search?query=vacina" | jq
```

#### Exemplo de resposta (JSON)

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
	"nextPageToken": ""
}
```

Notas sobre o schema:

- `claims` é uma lista; cada item pode conter campos adicionais retornados pelo serviço externo.
- `nextPageToken` pode vir vazio quando não há mais páginas.

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

