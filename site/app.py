from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session
import os
import json
from datetime import datetime
from fpdf import FPDF
import sys
from functools import wraps

# Adiciona o diretório atual ao path para importar módulos locais
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa o sistema de IA integrado
try:
    from sistema_ia_integrado import processar_pedido_educativo, obter_relatorio_sistema, exportar_conteudo_gerado
    from media_generate_image import gerar_imagem_desenho
    IA_DISPONIVEL = True
except ImportError as e:
    print(f"Aviso: Sistema de IA não disponível: {e}")
    IA_DISPONIVEL = False

# Importa o gerenciador de usuários
try:
    from gerenciador_usuarios import GerenciadorUsuarios
    gerenciador = GerenciadorUsuarios("/home/ubuntu/menteia/data/usuarios.json")
    USUARIOS_DISPONIVEL = True
except ImportError as e:
    print(f"Aviso: Sistema de usuários não disponível: {e}")
    USUARIOS_DISPONIVEL = False

app = Flask(__name__)

# Configurações
app.config['SECRET_KEY'] = 'sua_chave_secreta_muito_segura_aqui_2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Cria diretórios necessários
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Middleware para verificar autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'erro': 'Login necessário', 'redirect': '/login'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def verificar_creditos(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'erro': 'Login necessário'}), 401
        
        if not USUARIOS_DISPONIVEL:
            return jsonify({'erro': 'Sistema de usuários indisponível'}), 500
        
        user_id = session['user_id']
        limite_info = gerenciador.verificar_limite_geracao(user_id)
        
        if not limite_info.get('pode_gerar', False):
            return jsonify({
                'erro': 'Limite de gerações atingido',
                'limite_info': limite_info
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    """Página inicial"""
    return render_template("index.html")

@app.route("/gerar")
def gerar():
    """Página de geração de atividades"""
    return render_template("gerar.html")

@app.route("/gerar_atividade")
def gerar_atividade():
    """Página de geração de atividades específicas"""
    return render_template("gerar_atividade.html")

@app.route("/gerar_desenho")
def gerar_desenho():
    """Página de geração de desenhos"""
    return render_template("gerar_desenho.html")

@app.route("/gerar_jogo")
def gerar_jogo():
    """Página de geração de jogos"""
    return render_template("gerar_jogo.html")

@app.route("/gerar_livre")
def gerar_livre():
    """Página de geração livre"""
    return render_template("gerar_livre.html")

@app.route("/gerar_instrucoes")
def gerar_instrucoes():
    """Página de geração de instruções"""
    return render_template("gerar_instrucoes.html")

@app.route("/gerar_adaptada")
def gerar_adaptada():
    """Página de geração adaptada para TEA"""
    return render_template("gerar_adaptada.html")

@app.route("/gerar_tea_avancado")
def gerar_tea_avancado():
    """Página de geração avançada para TEA"""
    return render_template("gerar_tea_avancado.html")

@app.route("/historico")
def historico():
    """Página de histórico"""
    return render_template("historico.html")

@app.route("/painel")
@login_required
def painel():
    """Painel administrativo"""
    try:
        if not USUARIOS_DISPONIVEL:
            return render_template("painel.html", erro="Sistema de usuários não disponível")
        
        user_id = session['user_id']
        
        # Obtém informações do usuário
        usuario = gerenciador.obter_usuario(user_id)
        if not usuario:
            session.clear()
            return redirect(url_for('login'))
        
        # Obtém informações de limite
        limite_info = gerenciador.verificar_limite_geracao(user_id)
        
        # Obtém estatísticas
        estatisticas = gerenciador.obter_estatisticas_usuario(user_id)
        
        return render_template("painel.html", 
                             usuario=usuario,
                             limite_info=limite_info,
                             estatisticas=estatisticas)
        
    except Exception as e:
        return render_template("painel.html", erro=f"Erro interno: {str(e)}")

@app.route("/sobre")
def sobre():
    """Página sobre"""
    return render_template("sobre.html")

@app.route("/upgrade")
@login_required
def upgrade():
    """Página de upgrade de plano"""
    return render_template("upgrade.html")

@app.route("/login")
def login():
    """Página de login"""
    return render_template("login.html")

@app.route("/registro")
def registro():
    """Página de registro"""
    return render_template("registro.html")

@app.route("/logout")
def logout():
    """Logout do usuário"""
    session.clear()
    return redirect(url_for('index'))

# APIs de Autenticação

@app.route("/api/login", methods=["POST"])
def api_login():
    """API para fazer login"""
    try:
        print("=== DEBUG LOGIN API ===")
        print(f"USUARIOS_DISPONIVEL: {USUARIOS_DISPONIVEL}")
        
        if not USUARIOS_DISPONIVEL:
            print("Sistema de usuários não disponível")
            return jsonify({
                'sucesso': False,
                'erro': 'Sistema de usuários não disponível'
            }), 500
        
        dados = request.get_json()
        if not dados:
            dados = request.form.to_dict()
        
        print(f"Dados recebidos: {dados}")
        
        email = dados.get('email', '').strip()
        senha = dados.get('senha', '')
        
        print(f"Email extraído: '{email}'")
        print(f"Senha extraída: '{senha}'")
        
        if not email or not senha:
            print("Email ou senha vazios")
            return jsonify({
                'sucesso': False,
                'erro': 'E-mail e senha são obrigatórios'
            }), 400
        
        print("Chamando gerenciador.fazer_login...")
        resultado = gerenciador.fazer_login(email, senha)
        print(f"Resultado do gerenciador: {resultado}")
        
        if resultado['sucesso']:
            # Cria sessão
            session['user_id'] = resultado['usuario']['id']
            session['user_email'] = resultado['usuario']['email']
            session['user_nome'] = resultado['usuario']['nome']
            session['user_plano'] = resultado['usuario']['plano']
            
            print("Login bem-sucedido, criando sessão")
            
            return jsonify({
                'sucesso': True,
                'mensagem': 'Login realizado com sucesso',
                'usuario': {
                    'nome': resultado['usuario']['nome'],
                    'email': resultado['usuario']['email'],
                    'plano': resultado['usuario']['plano']
                },
                'redirect': '/painel'
            })
        else:
            print(f"Login falhou: {resultado}")
            return jsonify(resultado), 401
            
    except Exception as e:
        print(f"Erro na API de login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'sucesso': False,
            'erro': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/registro", methods=["POST"])
def api_registro():
    """API para registrar usuário"""
    try:
        if not USUARIOS_DISPONIVEL:
            return jsonify({
                'sucesso': False,
                'erro': 'Sistema de usuários não disponível'
            }), 500
        
        dados = request.get_json()
        if not dados:
            dados = request.form.to_dict()
        
        # Validações básicas
        campos_obrigatorios = ['nome', 'email', 'senha']
        for campo in campos_obrigatorios:
            if not dados.get(campo, '').strip():
                return jsonify({
                    'sucesso': False,
                    'erro': f'Campo {campo} é obrigatório'
                }), 400
        
        # Define plano padrão como free
        dados['plano'] = dados.get('plano', 'free')
        
        resultado = gerenciador.registrar_usuario(dados)
        
        if resultado['sucesso']:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Usuário registrado com sucesso',
                'redirect': '/login'
            })
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/usuario/info")
@login_required
def api_usuario_info():
    """API para obter informações do usuário logado"""
    try:
        if not USUARIOS_DISPONIVEL:
            return jsonify({'erro': 'Sistema de usuários não disponível'}), 500
        
        user_id = session['user_id']
        usuario = gerenciador.obter_usuario(user_id)
        
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        # Obtém informações de limite
        limite_info = gerenciador.verificar_limite_geracao(user_id)
        
        # Obtém estatísticas
        stats = gerenciador.obter_estatisticas_usuario(user_id)
        
        return jsonify({
            'usuario': usuario,
            'limites': limite_info,
            'estatisticas': stats
        })
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@app.route("/api/usuario/upgrade", methods=["POST"])
@login_required
def api_upgrade_plano():
    """API para fazer upgrade do plano"""
    try:
        if not USUARIOS_DISPONIVEL:
            return jsonify({'erro': 'Sistema de usuários não disponível'}), 500
        
        dados = request.get_json()
        novo_plano = dados.get('plano', '')
        simulacao = dados.get('simulacao', False)
        
        if novo_plano not in ['premium', 'escola']:
            return jsonify({'erro': 'Plano inválido'}), 400
        
        user_id = session['user_id']
        
        # Se for simulação, apenas atualiza o plano sem validar pagamento
        if simulacao:
            resultado = gerenciador.atualizar_plano(user_id, novo_plano)
            
            if resultado['sucesso']:
                # Atualiza sessão
                session['user_plano'] = novo_plano
                
                # Adiciona informações de "pagamento" simulado
                resultado['pagamento'] = {
                    'status': 'aprovado',
                    'metodo': 'simulacao',
                    'valor': 19.00 if novo_plano == 'premium' else 99.00,
                    'data': datetime.now().isoformat()
                }
                
                # Log da simulação
                print(f"[SIMULAÇÃO] Upgrade realizado para usuário {user_id}: {novo_plano}")
            
            return jsonify(resultado)
        else:
            # Aqui seria implementada a integração real com gateway de pagamento
            return jsonify({'erro': 'Pagamento real não implementado nesta versão'}), 501
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

# APIs para geração de conteúdo

@app.route("/api/gerar_conteudo", methods=["POST"])
@verificar_creditos
def api_gerar_conteudo():
    """API para gerar conteúdo educativo inteligente"""
    try:
        if not IA_DISPONIVEL:
            return jsonify({
                'sucesso': False,
                'erro': 'Sistema de IA não disponível'
            }), 500
        
        dados = request.get_json()
        if not dados:
            dados = request.form.to_dict()
        
        pedido = dados.get('pedido', '')
        incluir_imagem = dados.get('incluir_imagem', True)
        
        if not pedido:
            return jsonify({
                'sucesso': False,
                'erro': 'Pedido não fornecido'
            }), 400
        
        # Processa o pedido com o sistema de IA
        resultado = processar_pedido_educativo(pedido, incluir_imagem)
        
        # Se sucesso, registra a geração
        if resultado.get('sucesso') and USUARIOS_DISPONIVEL:
            user_id = session['user_id']
            gerenciador.registrar_geracao(user_id, 'conteudo_geral', {
                'pedido': pedido,
                'incluir_imagem': incluir_imagem
            })
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/gerar_desenho", methods=["POST"])
@verificar_creditos
def api_gerar_desenho():
    """API específica para gerar desenhos para colorir"""
    try:
        dados = request.get_json()
        if not dados:
            dados = request.form.to_dict()
        
        tema = dados.get('tema', '')
        estilo = dados.get('estilo', 'simples')
        idade = dados.get('idade_desenho', '6-8 anos')
        
        if not tema:
            return jsonify({
                'sucesso': False,
                'erro': 'Tema não fornecido'
            }), 400
        
        # Constrói prompt específico para desenho
        prompt = f"Desenho para colorir sobre {tema}, estilo {estilo}, para idade {idade}"
        
        if IA_DISPONIVEL:
            resultado = processar_pedido_educativo(prompt, incluir_imagem=True)
            
            # Se sucesso, registra a geração
            if resultado.get('sucesso') and USUARIOS_DISPONIVEL:
                user_id = session['user_id']
                gerenciador.registrar_geracao(user_id, 'desenho', {
                    'tema': tema,
                    'estilo': estilo,
                    'idade': idade
                })
            
            return jsonify(resultado)
        else:
            # Fallback para sistema básico
            caminho_arquivo = f"static/images/desenho_{tema.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            sucesso = gerar_imagem_desenho(prompt, caminho_arquivo)
            
            # Se sucesso, registra a geração
            if sucesso and USUARIOS_DISPONIVEL:
                user_id = session['user_id']
                gerenciador.registrar_geracao(user_id, 'desenho', {
                    'tema': tema,
                    'estilo': estilo,
                    'idade': idade
                })
            
            return jsonify({
                'sucesso': sucesso,
                'caminho_arquivo': caminho_arquivo if sucesso else None,
                'prompt_usado': prompt
            })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/gerar_jogo", methods=["POST"])
@verificar_creditos
def api_gerar_jogo():
    """API para gerar jogos educativos"""
    try:
        dados = request.get_json()
        if not dados:
            dados = request.form.to_dict()
        
        tema = dados.get('tema', '')
        tipo_jogo = dados.get('tipo_jogo', 'Quiz')
        idade = dados.get('idade', '6-8 anos')
        participantes = dados.get('participantes', '1-4 jogadores')
        
        if not tema:
            return jsonify({
                'sucesso': False,
                'erro': 'Tema não fornecido'
            }), 400
        
        # Constrói prompt específico para jogo
        prompt = f"Jogo educativo tipo {tipo_jogo} sobre {tema} para {idade} com {participantes}"
        
        if IA_DISPONIVEL:
            resultado = processar_pedido_educativo(prompt, incluir_imagem=False)
            
            # Se sucesso, registra a geração
            if resultado.get('sucesso') and USUARIOS_DISPONIVEL:
                user_id = session['user_id']
                gerenciador.registrar_geracao(user_id, 'jogo', {
                    'tema': tema,
                    'tipo_jogo': tipo_jogo,
                    'idade': idade,
                    'participantes': participantes
                })
            
            return jsonify(resultado)
        else:
            # Fallback para sistema básico
            from geradores_especiais import gerar_jogo_educativo
            conteudo = gerar_jogo_educativo(tema, tipo_jogo, idade, participantes)
            
            # Se sucesso, registra a geração
            if USUARIOS_DISPONIVEL:
                user_id = session['user_id']
                gerenciador.registrar_geracao(user_id, 'jogo', {
                    'tema': tema,
                    'tipo_jogo': tipo_jogo,
                    'idade': idade,
                    'participantes': participantes
                })
            
            return jsonify({
                'sucesso': True,
                'conteudo_texto': {
                    'conteudo_gerado': conteudo,
                    'template_usado': f'Jogo {tipo_jogo}',
                    'qualidade_estimada': {'nivel': 'Bom', 'score_geral': 0.7}
                }
            })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/gerar_atividade_tea", methods=["POST"])
@verificar_creditos
def api_gerar_atividade_tea():
    """API específica para gerar atividades adaptadas para TEA"""
    try:
        dados = request.get_json()
        if not dados:
            dados = request.form.to_dict()
        
        tema = dados.get('tema', '')
        nivel = dados.get('nivel', 'básico')
        interesse = dados.get('interesse', '')
        sensibilidade = dados.get('sensibilidade', '')
        
        if not tema:
            return jsonify({
                'sucesso': False,
                'erro': 'Tema não fornecido'
            }), 400
        
        # Constrói prompt específico para TEA
        prompt = f"Atividade para criança com TEA sobre {tema}, nível {nivel}"
        if interesse:
            prompt += f", considerando interesse em {interesse}"
        if sensibilidade:
            prompt += f", com cuidados para {sensibilidade}"
        
        if IA_DISPONIVEL:
            resultado = processar_pedido_educativo(prompt, incluir_imagem=True)
            
            # Se sucesso, registra a geração
            if resultado.get('sucesso') and USUARIOS_DISPONIVEL:
                user_id = session['user_id']
                gerenciador.registrar_geracao(user_id, 'atividade_tea', {
                    'tema': tema,
                    'nivel': nivel,
                    'interesse': interesse,
                    'sensibilidade': sensibilidade
                })
            
            return jsonify(resultado)
        else:
            return jsonify({
                'sucesso': False,
                'erro': 'Sistema de IA para TEA não disponível'
            }), 500
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/relatorio_sistema")
def api_relatorio_sistema():
    """API para obter relatório do sistema"""
    try:
        if not IA_DISPONIVEL:
            return jsonify({
                'erro': 'Sistema de IA não disponível'
            }), 500
        
        relatorio = obter_relatorio_sistema()
        return jsonify(relatorio)
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro interno: {str(e)}'
        }), 500

@app.route("/api/exportar_conteudo/<id_geracao>")
def api_exportar_conteudo(id_geracao):
    """API para exportar conteúdo gerado"""
    try:
        if not IA_DISPONIVEL:
            return jsonify({
                'erro': 'Sistema de IA não disponível'
            }), 500
        
        formato = request.args.get('formato', 'markdown')
        conteudo = exportar_conteudo_gerado(id_geracao, formato)
        
        if conteudo == "Geração não encontrada":
            return jsonify({
                'erro': 'Conteúdo não encontrado'
            }), 404
        
        return jsonify({
            'conteudo': conteudo,
            'formato': formato
        })
        
    except Exception as e:
        return jsonify({
            'erro': f'Erro interno: {str(e)}'
        }), 500

# Rota original mantida para compatibilidade
@app.route("/gerar_original", methods=["POST"])
def gerar_original():
    """Rota original de geração (mantida para compatibilidade)"""
    try:
        nome = request.form.get("nome", "Criança")
        preferencia = request.form.get("preferencia", "atividades gerais")
        quantidade = int(request.form.get("quantidade", 1))

        # Usa o novo sistema se disponível
        if IA_DISPONIVEL:
            pedido = f"Criar {quantidade} atividades para {nome} que gosta de {preferencia}"
            resultado = processar_pedido_educativo(pedido, incluir_imagem=False)
            
            if resultado['sucesso']:
                conteudo = resultado['conteudo_texto']['conteudo_gerado']
                
                # Gera PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Atividades para {nome}", ln=True, align='C')
                
                # Adiciona conteúdo (tratamento básico para caracteres especiais)
                try:
                    pdf.multi_cell(0, 10, txt=conteudo.encode('latin-1', 'replace').decode('latin-1'))
                except:
                    pdf.multi_cell(0, 10, txt="Conteúdo gerado com sucesso (caracteres especiais removidos)")
                
                output_path = f"data/atividades_{nome}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf.output(output_path)
                
                return send_file(output_path, as_attachment=True)
            else:
                return f"Erro na geração: {resultado.get('erro', 'Erro desconhecido')}", 500
        else:
            return "Sistema de IA não disponível", 500
            
    except Exception as e:
        return f"Erro interno: {str(e)}", 500

@app.errorhandler(404)
def not_found(error):
    """Página de erro 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Página de erro 500"""
    return render_template('500.html'), 500

if __name__ == "__main__":
    print("🚀 Iniciando AtivaMente - Sistema de IA Educativa")
    print(f"📊 Sistema de IA: {'✅ Disponível' if IA_DISPONIVEL else '❌ Não disponível'}")
    print(f"👥 Sistema de Usuários: {'✅ Disponível' if USUARIOS_DISPONIVEL else '❌ Não disponível'}")
    print("🌐 Acesse: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=True)

