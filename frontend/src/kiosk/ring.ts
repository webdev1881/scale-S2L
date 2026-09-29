/**
 * Звонок механического телефона — одноразовый сигнал к «Заберіть товар з
 * платформи»: тост можно не заметить, стоя в стороне, а звук слышен по всему
 * залу. Звук синтезируется на лету (Web Audio), а не грузится файлом: старый
 * дребезжащий звонок — это несущий тон, промодулированный по амплитуде
 * быстрым тремоло (~22 Гц), а не запись, и так короче и без лицензионных
 * вопросов к аудиофайлу.
 *
 * `AudioContext` создаётся и разблокируется в первом касании экрана
 * (`unlockRingAudio`, дергается из `engage()`) — браузер не даст звуку играть
 * без жеста пользователя, а к моменту звонка касание почти наверняка уже было.
 */
let ctx: AudioContext | null = null

export function unlockRingAudio() {
  if (!ctx) ctx = new AudioContext()
  if (ctx.state === 'suspended') void ctx.resume()
}

export function playTakeGoodsRing(durationS: number) {
  if (!ctx || durationS <= 0) return
  if (ctx.state === 'suspended') void ctx.resume()

  const now = ctx.currentTime
  const attack = 0.015
  const release = 0.05
  const end = now + durationS

  // Несущие тона — гармоники, похожие на механический звонок; два тона вместе
  // звучат «металлически», один синус — слишком гладко и не похоже на звонок.
  const mix = ctx.createGain()
  mix.gain.value = 0.5
  for (const freq of [950, 1400]) {
    const carrier = ctx.createOscillator()
    carrier.type = 'square'
    carrier.frequency.value = freq
    carrier.connect(mix)
    carrier.start(now)
    carrier.stop(end)
  }

  // Тремоло: несущая амплитуда дрожит на ~22 Гц — тот самый дребезг звонка,
  // а не ровный гудок.
  const trill = ctx.createGain()
  trill.gain.value = 0.5
  const lfo = ctx.createOscillator()
  lfo.frequency.value = 22
  const lfoDepth = ctx.createGain()
  lfoDepth.gain.value = 0.5
  lfo.connect(lfoDepth)
  lfoDepth.connect(trill.gain)
  lfo.start(now)
  lfo.stop(end)

  // Общая огибающая — короткая атака и спад, чтобы не щёлкало на границах.
  const envelope = ctx.createGain()
  envelope.gain.setValueAtTime(0, now)
  envelope.gain.linearRampToValueAtTime(0.5, now + attack)
  envelope.gain.setValueAtTime(0.5, Math.max(now + attack, end - release))
  envelope.gain.linearRampToValueAtTime(0, end)

  mix.connect(trill)
  trill.connect(envelope)
  envelope.connect(ctx.destination)
}
