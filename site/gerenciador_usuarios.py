import os
import json
import hashlib
import datetime
from typing import Dict, List, Optional, Any
import uuid

class GerenciadorUsuarios:
    """
    Sistema de gerenciamento de usuários com controle de limites de geração
    """
    
    def __init__(self, arquivo_usuarios: str = "/home/ubuntu/site_tea/data/usuarios.json"):
        self.arquivo_usuarios = arquivo_usuarios
        self.usuarios = self._carregar_usuarios()
        
        # Cria diretório se não existir
        os.makedirs(os.path.dirname(arquivo_usuarios), exist_ok=True)
    
    def _carregar_usuarios(self) -> Dict[str, Any]:
        """Carrega usuários do arquivo JSON"""
        try:
            if os.path.exists(self.arquivo_usuarios):
                with open(self.arquivo_usuarios, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar usuários: {e}")
        
        return {}
    
    def _salvar_usuarios(self) -> bool:
        """Salva usuários no arquivo JSON"""
        try:
            with open(self.arquivo_usuarios, 'w', encoding='utf-8') as f:
                json.dump(self.usuarios, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Erro ao salvar usuários: {e}")
            return False
    
    def _hash_senha(self, senha: str) -> str:
        """Gera hash da senha"""
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def _gerar_id_usuario(self) -> str:
        """Gera ID único para usuário"""
        return str(uuid.uuid4())
    
    def registrar_usuario(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra um novo usuário
        """
        try:
            # Validações básicas
            if not dados.get('email') or not dados.get('senha') or not dados.get('nome'):
                return {"sucesso": False, "erro": "Campos obrigatórios não preenchidos"}
            
            email = dados['email'].lower().strip()
            
            # Verifica se email já existe
            if self._email_existe(email):
                return {"sucesso": False, "erro": "E-mail já cadastrado"}
            
            # Valida senha
            if len(dados['senha']) < 6:
                return {"sucesso": False, "erro": "Senha deve ter pelo menos 6 caracteres"}
            
            # Cria usuário
            user_id = self._gerar_id_usuario()
            agora = datetime.datetime.now()
            
            usuario = {
                "id": user_id,
                "nome": dados['nome'].strip(),
                "email": email,
                "senha_hash": self._hash_senha(dados['senha']),
                "telefone": dados.get('telefone', ''),
                "data_nascimento": dados.get('data_nascimento', ''),
                "profissao": dados.get('profissao', ''),
                "instituicao": dados.get('instituicao', ''),
                "cidade": dados.get('cidade', ''),
                "estado": dados.get('estado', ''),
                "plano": dados.get('plano', 'free'),
                "como_conheceu": dados.get('como_conheceu', ''),
                "aceitar_termos": dados.get('aceitar_termos', False),
                "aceitar_newsletter": dados.get('aceitar_newsletter', False),
                "data_cadastro": agora.isoformat(),
                "ultimo_login": None,
                "ativo": True,
                "limites_geracao": self._inicializar_limites(dados.get('plano', 'free')),
                "historico_geracoes": [],
                "configuracoes": {
                    "tema_preferido": "claro",
                    "notificacoes": True,
                    "idioma": "pt-BR"
                }
            }
            
            # Salva usuário
            self.usuarios[user_id] = usuario
            
            if self._salvar_usuarios():
                return {
                    "sucesso": True,
                    "usuario_id": user_id,
                    "mensagem": "Usuário registrado com sucesso"
                }
            else:
                return {"sucesso": False, "erro": "Erro ao salvar usuário"}
                
        except Exception as e:
            return {"sucesso": False, "erro": f"Erro interno: {str(e)}"}
    
    def _email_existe(self, email: str) -> bool:
        """Verifica se email já existe"""
        for usuario in self.usuarios.values():
            if usuario.get('email', '').lower() == email.lower():
                return True
        return False
    
    def _inicializar_limites(self, plano: str) -> Dict[str, Any]:
        """Inicializa limites de geração baseado no plano"""
        agora = datetime.datetime.now()
        
        if plano == 'free':
            return {
                "plano": "free",
                "geracoes_por_dia": 1,
                "geracoes_hoje": 0,
                "ultimo_reset": agora.date().isoformat(),
                "total_geracoes": 0,
                "limite_mensal": 30,
                "geracoes_mes": 0,
                "ultimo_reset_mensal": agora.replace(day=1).date().isoformat()
            }
        elif plano == 'premium':
            return {
                "plano": "premium",
                "geracoes_por_dia": 10,  # 10 gerações por dia para premium
                "geracoes_hoje": 0,
                "ultimo_reset": agora.date().isoformat(),
                "total_geracoes": 0,
                "limite_mensal": 300,  # 10 * 30 dias
                "geracoes_mes": 0,
                "ultimo_reset_mensal": agora.replace(day=1).date().isoformat()
            }
        elif plano == 'escola':
            return {
                "plano": "escola",
                "geracoes_por_dia": -1,  # -1 = ilimitado
                "geracoes_hoje": 0,
                "ultimo_reset": agora.date().isoformat(),
                "total_geracoes": 0,
                "limite_mensal": -1,  # -1 = ilimitado
                "geracoes_mes": 0,
                "ultimo_reset_mensal": agora.replace(day=1).date().isoformat(),
                "professores_max": 50,
                "professores_ativos": 1
            }
        else:
            return self._inicializar_limites('free')
    
    def fazer_login(self, email: str, senha: str) -> Dict[str, Any]:
        """
        Realiza login do usuário
        """
        try:
            email = email.lower().strip()
            senha_hash = self._hash_senha(senha)
            
            # Busca usuário por email
            usuario = None
            for user_data in self.usuarios.values():
                if user_data.get('email', '').lower() == email:
                    usuario = user_data
                    break
            
            if not usuario:
                return {"sucesso": False, "erro": "E-mail não encontrado"}
            
            if not usuario.get('ativo', False):
                return {"sucesso": False, "erro": "Conta desativada"}
            
            if usuario.get('senha_hash') != senha_hash:
                return {"sucesso": False, "erro": "Senha incorreta"}
            
            # Atualiza último login
            usuario['ultimo_login'] = datetime.datetime.now().isoformat()
            self._salvar_usuarios()
            
            # Remove dados sensíveis da resposta
            usuario_seguro = {k: v for k, v in usuario.items() if k != 'senha_hash'}
            
            return {
                "sucesso": True,
                "usuario": usuario_seguro,
                "mensagem": "Login realizado com sucesso"
            }
            
        except Exception as e:
            return {"sucesso": False, "erro": f"Erro interno: {str(e)}"}
    
    def obter_usuario(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Obtém dados do usuário por ID"""
        usuario = self.usuarios.get(user_id)
        if usuario:
            # Remove dados sensíveis
            return {k: v for k, v in usuario.items() if k != 'senha_hash'}
        return None
    
    def verificar_limite_geracao(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica se usuário pode gerar conteúdo
        """
        try:
            usuario = self.usuarios.get(user_id)
            if not usuario:
                return {"pode_gerar": False, "erro": "Usuário não encontrado"}
            
            limites = usuario.get('limites_geracao', {})
            agora = datetime.datetime.now()
            hoje = agora.date().isoformat()
            
            # Reset diário se necessário
            if limites.get('ultimo_reset') != hoje:
                limites['geracoes_hoje'] = 0
                limites['ultimo_reset'] = hoje
            
            # Reset mensal se necessário
            primeiro_dia_mes = agora.replace(day=1).date().isoformat()
            if limites.get('ultimo_reset_mensal') != primeiro_dia_mes:
                limites['geracoes_mes'] = 0
                limites['ultimo_reset_mensal'] = primeiro_dia_mes
            
            plano = limites.get('plano', 'free')
            geracoes_hoje = limites.get('geracoes_hoje', 0)
            limite_diario = limites.get('geracoes_por_dia', 1)
            
            # Verifica limite
            if limite_diario == -1:  # Ilimitado
                pode_gerar = True
                restantes = -1
            else:
                pode_gerar = geracoes_hoje < limite_diario
                restantes = max(0, limite_diario - geracoes_hoje)
            
            return {
                "pode_gerar": pode_gerar,
                "plano": plano,
                "geracoes_hoje": geracoes_hoje,
                "limite_diario": limite_diario,
                "geracoes_restantes": restantes,
                "proximo_reset": "00:00 (meia-noite)"
            }
            
        except Exception as e:
            return {"pode_gerar": False, "erro": f"Erro interno: {str(e)}"}
    
    def registrar_geracao(self, user_id: str, tipo_geracao: str, detalhes: Dict[str, Any] = None) -> bool:
        """
        Registra uma geração realizada pelo usuário
        """
        try:
            usuario = self.usuarios.get(user_id)
            if not usuario:
                return False
            
            agora = datetime.datetime.now()
            
            # Atualiza contadores
            limites = usuario.get('limites_geracao', {})
            limites['geracoes_hoje'] = limites.get('geracoes_hoje', 0) + 1
            limites['geracoes_mes'] = limites.get('geracoes_mes', 0) + 1
            limites['total_geracoes'] = limites.get('total_geracoes', 0) + 1
            
            # Adiciona ao histórico
            if 'historico_geracoes' not in usuario:
                usuario['historico_geracoes'] = []
            
            registro_geracao = {
                "id": str(uuid.uuid4()),
                "tipo": tipo_geracao,
                "timestamp": agora.isoformat(),
                "detalhes": detalhes or {},
                "sucesso": True
            }
            
            usuario['historico_geracoes'].append(registro_geracao)
            
            # Mantém apenas os últimos 100 registros
            if len(usuario['historico_geracoes']) > 100:
                usuario['historico_geracoes'] = usuario['historico_geracoes'][-100:]
            
            return self._salvar_usuarios()
            
        except Exception as e:
            print(f"Erro ao registrar geração: {e}")
            return False
    
    def obter_estatisticas_usuario(self, user_id: str) -> Dict[str, Any]:
        """
        Obtém estatísticas do usuário
        """
        try:
            usuario = self.usuarios.get(user_id)
            if not usuario:
                return {"erro": "Usuário não encontrado"}
            
            limites = usuario.get('limites_geracao', {})
            historico = usuario.get('historico_geracoes', [])
            
            # Estatísticas básicas
            stats = {
                "total_geracoes": limites.get('total_geracoes', 0),
                "geracoes_hoje": limites.get('geracoes_hoje', 0),
                "geracoes_mes": limites.get('geracoes_mes', 0),
                "plano": limites.get('plano', 'free'),
                "membro_desde": usuario.get('data_cadastro', ''),
                "ultimo_login": usuario.get('ultimo_login', ''),
                "historico_recente": historico[-10:] if historico else []
            }
            
            # Estatísticas por tipo
            tipos_geracao = {}
            for registro in historico:
                tipo = registro.get('tipo', 'desconhecido')
                tipos_geracao[tipo] = tipos_geracao.get(tipo, 0) + 1
            
            stats['tipos_geracao'] = tipos_geracao
            
            return stats
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    def atualizar_plano(self, user_id: str, novo_plano: str) -> Dict[str, Any]:
        """
        Atualiza plano do usuário
        """
        try:
            usuario = self.usuarios.get(user_id)
            if not usuario:
                return {"sucesso": False, "erro": "Usuário não encontrado"}
            
            planos_validos = ['free', 'premium', 'escola']
            if novo_plano not in planos_validos:
                return {"sucesso": False, "erro": "Plano inválido"}
            
            # Atualiza plano e limites
            usuario['plano'] = novo_plano
            usuario['limites_geracao'] = self._inicializar_limites(novo_plano)
            
            if self._salvar_usuarios():
                return {
                    "sucesso": True,
                    "mensagem": f"Plano atualizado para {novo_plano}",
                    "novos_limites": usuario['limites_geracao']
                }
            else:
                return {"sucesso": False, "erro": "Erro ao salvar alterações"}
                
        except Exception as e:
            return {"sucesso": False, "erro": f"Erro interno: {str(e)}"}
    
    def listar_usuarios(self, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        """
        Lista usuários (sem dados sensíveis)
        """
        usuarios_lista = []
        
        for usuario in self.usuarios.values():
            if apenas_ativos and not usuario.get('ativo', False):
                continue
            
            # Remove dados sensíveis
            usuario_seguro = {
                "id": usuario.get('id'),
                "nome": usuario.get('nome'),
                "email": usuario.get('email'),
                "plano": usuario.get('plano'),
                "data_cadastro": usuario.get('data_cadastro'),
                "ultimo_login": usuario.get('ultimo_login'),
                "total_geracoes": usuario.get('limites_geracao', {}).get('total_geracoes', 0)
            }
            usuarios_lista.append(usuario_seguro)
        
        return usuarios_lista
    
    def obter_estatisticas_gerais(self) -> Dict[str, Any]:
        """
        Obtém estatísticas gerais da plataforma
        """
        try:
            total_usuarios = len(self.usuarios)
            usuarios_ativos = sum(1 for u in self.usuarios.values() if u.get('ativo', False))
            
            # Contagem por plano
            planos = {'free': 0, 'premium': 0, 'escola': 0}
            total_geracoes = 0
            
            for usuario in self.usuarios.values():
                if usuario.get('ativo', False):
                    plano = usuario.get('plano', 'free')
                    planos[plano] = planos.get(plano, 0) + 1
                    total_geracoes += usuario.get('limites_geracao', {}).get('total_geracoes', 0)
            
            return {
                "total_usuarios": total_usuarios,
                "usuarios_ativos": usuarios_ativos,
                "distribuicao_planos": planos,
                "total_geracoes": total_geracoes,
                "media_geracoes_por_usuario": total_geracoes / max(usuarios_ativos, 1)
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}


# Instância global do gerenciador
gerenciador_usuarios = GerenciadorUsuarios()

