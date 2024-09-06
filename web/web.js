import {app} from '../../../scripts/app.js'
import {api} from '../../../scripts/api.js'
import {$el} from '../../../scripts/ui.js'

const styleElement = document.createElement("style")
const cssCode = `
    #loadingDiv{
        width:720px;
        height: 480px;
        text-align: center;
        font-size: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    #toastDiv{
        width:640px;
        height: 320px;
        text-align: center;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .publish_btn {
      flex:1;
      height:30px;
      border-radius: 8px;
      border: 2px solid var(--border-color);
      font-size:11px;
      background:var(--comfy-input-bg);
      box-shadow:none;
      cursor:pointer;
      width: 1rem;
    }
    .publish_btn:hover {
        transform: scale(1.1);
    }
    .publish_btn:active {
        transform: scale(0.95);
    }
    #publish_btn {
      max-height: 80px;
      display:flex;
      flex-wrap: wrap;
      align-items: flex-start;
    }
    .uniqueid {
      display: none;
    }
    #showMsgDiv {
      width:800px;
      padding: 60px 0;
      text-align: center;
      font-size: 30px;
      color: var(--fg-color);
    }
    .loginBox {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px;
        background-color: var(--comfy-input-bg);
        border-radius: 8px;
        width: 300px;
      }
      .loginInput {
        margin: 10px 0;
        padding: 8px;
        width: 100%;
        border: 1px solid var(--border-color);
        border-radius: 4px;
      }
      .loginButton {
        margin-top: 10px;
        padding: 10px;
        width: 100%;
        background-color: var(--border-color);
        color: var(--input-text);
        border-radius: 4px;
        cursor: pointer;
      }
`
styleElement.innerHTML = cssCode
document.head.appendChild(styleElement)

app.ui.dialog.element.style.zIndex = 10001
///////////////////////// loading /////////////////////////
var loading = false
const loadingDiv = $el('div', {id: 'loadingDiv'}, '')
const loadingBox = $el("div.comfy-modal", {parent: document.body}, [])
loadingBox.appendChild(loadingDiv)
loadingBox.style.display = "none"
loadingBox.style.zIndex = 10011
function showLoading(msg = '') {
    loadingDiv.innerText = msg ? msg : '拼命执行中，请稍等...'
    loadingBox.style.display = "block"
    loading = true
}
function hideLoading() {
    loadingBox.style.display = "none"
    loading = false
}
///////////////////////// toast /////////////////////////
const toastDiv = $el('div', {id: 'toastDiv'}, '')
const toastBox = $el("div.comfy-modal", {parent: document.body}, [])
toastBox.appendChild(toastDiv)
toastBox.style.display = "none"
toastBox.style.zIndex = 10021
function showToast(msg = '', stay_time = 0, color = 'white') {
    stay_time = stay_time > 0 ? stay_time : 2000
    toastDiv.innerText = msg ? msg : ''
    toastBox.style.display = "block"
    toastBox.style.color = color
    setTimeout(() => {
        toastBox.style.color = "white"
        toastBox.style.display = "none"
    }, stay_time)
}
///////////////////////// message /////////////////////////
const showMsgDiv = $el('div', {id: 'showMsgDiv'}, '')
function showMsg(msg, color = 'white') {
    showMsgDiv.style.color = color
    showMsgDiv.innerText = msg
    app.ui.dialog.show(showMsgDiv)
}
///////////////////////// login /////////////////////////
const loginBox = $el('div.loginBox', {}, [
    $el('input', {
        type: 'text',
        placeholder: 'Username',
        className: 'loginInput'
    }),
    $el('input', {
        type: 'password',
        placeholder: 'Password',
        className: 'loginInput'
    }),
    $el('button', {
        className: 'loginButton',
        onclick: async function() {
            let result = await login(loginBox.children[0].value, loginBox.children[1].value)
            if (result) {
                showToast(result, 2000, "red")
            } else {
                setTimeout(() => {
                    app.ui.dialog.close(loginBox)
                }, 500)
                showToast("success", 2000, "green")
            }
        }
    }, 'Login')
]);

async function check(){
    const response = await api.fetchApi(`/check`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data: ""})
    })
    const result = await response.json()
    return result.userInfo
}

async function login(username, password) {
    if (username == '') {
        return "username can not be empty"
    }
    if (password == '') {
        return "password can not be empty"
    }
    const prompt = await app.graphToPrompt()
    const response = await api.fetchApi(`/login`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ prompt: prompt, username: username, password: password })
    })
    const result = await response.json()
    // console.log(">>>>>>>>>>>>>>>>>>>>>>>> login result:", result)
    return result.message
}

async function publish() {
    const prompt = await app.graphToPrompt()
    const response = await api.fetchApi(`/add_workflow`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data: prompt})
    })
    const result = await response.json()
    return result
}

app.registerExtension({
    name: 'klNodeHandler',
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "klImage" ||
            nodeData.name === "klText" ||
            nodeData.name === "klText1" ||
            nodeData.name === "klInt" ||
            nodeData.name === "klSize" ||
            nodeData.name === "klBool") {
            const onNodeCreated = nodeType.prototype.onNodeCreated
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated?.apply(this, arguments) : undefined
                if (this.bgcolor === undefined || this.bgcolor === "") {
                    this.bgcolor = "#353"
                }
                return r
            }
        }
        if (nodeData.name === 'klPublisher') {
            const onNodeCreated = nodeType.prototype.onNodeCreated
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated?.apply(this, arguments) : undefined
                check().then(userInfo => {
                    const auw = this.widgets.find(w => w.name === 'APIUrl')
                    if(auw && auw.value === '' && userInfo !== null && userInfo.APIUrl !== null) {
                        auw.value = userInfo.APIUrl
                    }
                }).catch(error => {
                    showMsg(error, "red")
                })
                this.addDOMWidget('select_styles', "btn", $el('div', { id: 'publish_btn' }, [
                    $el('button.publish_btn', {
                        textContent: '发布 / 更新',
                        style: { color:'green' },
                        onclick: async () => {
                            if(loading){
                                return
                            }
                            const auw = this.widgets.find(w => w.name === 'APIUrl')
                            if(auw.value === '') {
                                showMsg("setup \'APIUrl\' first", "red")
                                return
                            }
                            const tw = this.widgets.find(w => w.name === 'Tittle')
                            if(tw.value === '') {
                                showMsg("setup \'Title\' first", "red")
                                return
                            }
                            const dw = this.widgets.find(w => w.name === 'Describe')
                            if(dw.value === '') {
                                showMsg("setup \'Describe\' first", "red")
                                return
                            }
                            const userInfo = await check()
                            if (userInfo === null) {
                                app.ui.dialog.show(loginBox)
                                return
                            }
                            app.ui.dialog.close()
                            try {
                                showLoading()
                                let response = await publish()
                                if (response.resultType === 1){
                                    hideLoading()
                                    showMsg(response.message, "red")
                                } else if (response.resultType === 2) {
                                    hideLoading()
                                    app.ui.dialog.show(loginBox)
                                } else {
                                    const widget = this.widgets.find(w => w.name === 'ID')
                                    if (widget) {
                                        widget.value = response.message
                                        setTimeout(() => {
                                            hideLoading()
                                            showToast(response.resultType === 5 ? "更新成功" : "发布成功", 2000, "green")
                                        }, 300)
                                    } else {
                                        hideLoading()
                                        showMsg("内部错误", "red")
                                    }
                                }
                            } catch (err) {
                                hideLoading()
                                showMsg(err, "red")
                            }
                        }
                    }),
                ]))
                this.computeSize()
                return r
            }
            nodeType.prototype.onRemoved = function () {
                console.log("Node delected:", this)
            }
        }
    }
})
