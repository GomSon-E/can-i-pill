import { useState, useEffect } from 'react'

function SignalIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="11" viewBox="0 0 16 11" fill="currentColor">
      <rect x="0" y="6" width="3" height="5" rx="0.5" />
      <rect x="4.5" y="4" width="3" height="7" rx="0.5" />
      <rect x="9" y="2" width="3" height="9" rx="0.5" />
      <rect x="13.5" y="0" width="2.5" height="11" rx="0.5" />
    </svg>
  )
}

function BatteryIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="11" viewBox="0 0 22 11" fill="none">
      <rect x="0.5" y="0.5" width="18" height="10" rx="2.5" stroke="currentColor" />
      <rect x="2" y="2" width="15" height="7" rx="1.5" fill="currentColor" />
      <rect x="19.5" y="3.5" width="1.5" height="4" rx="0.5" fill="currentColor" />
    </svg>
  )
}

function useClock() {
  const fmt = () => {
    const now = new Date()
    return `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
  }
  const [time, setTime] = useState(fmt)
  useEffect(() => {
    const id = setInterval(() => setTime(fmt()), 1000)
    return () => clearInterval(id)
  }, [])
  return time
}

export default function StatusBar() {
  const time = useClock()
  return (
    <div style={{
      height: 32,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingLeft: 22,
      paddingRight: 22,
      flexShrink: 0,
    }}>
      <span style={{ fontSize: 13, fontWeight: 600, color: '#1A1B22' }}>{time}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#1A1B22' }}>
        <SignalIcon />
        <BatteryIcon />
      </div>
    </div>
  )
}
