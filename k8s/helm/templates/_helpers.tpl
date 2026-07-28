{{/*
Common labels for all resources
*/}}
{{- define "alphaforge.labels" -}}
app.kubernetes.io/name: {{ .Values.global.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/part-of: alphaforge
{{- end }}

{{/*
Backend labels
*/}}
{{- define "alphaforge.backend.labels" -}}
{{ include "alphaforge.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "alphaforge.frontend.labels" -}}
{{ include "alphaforge.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Selector labels
*/}}
{{- define "alphaforge.selectorLabels" -}}
app.kubernetes.io/name: {{ .Values.global.name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "alphaforge.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default "alphaforge" .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
