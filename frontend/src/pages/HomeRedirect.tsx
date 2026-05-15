import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function HomeRedirect() {
  const navigate = useNavigate()

  useEffect(() => {
    const onboardingComplete = localStorage.getItem('onboardingComplete')
    if (onboardingComplete === 'true') {
      navigate('/main-01', { replace: true })
    } else {
      navigate('/intro-01', { replace: true })
    }
  }, [navigate])

  return null
}
