import { Routes, Route, Navigate } from 'react-router-dom'
import Intro01 from './pages/intro/Intro01'
import Intro02 from './pages/intro/Intro02'
import Intro03 from './pages/intro/Intro03'
import Ob01 from './pages/ob/Ob01'
import Ob02 from './pages/ob/Ob02'
import Ob03 from './pages/ob/Ob03'
import Ob04 from './pages/ob/Ob04'
import Ob05 from './pages/ob/Ob05'
import Main01 from './pages/main/Main01'
import Main02 from './pages/main/Main02'
import Main03 from './pages/main/Main03'
import Main04 from './pages/main/Main04'
import Main05 from './pages/main/Main05'
import Sub01 from './pages/sub/Sub01'
import Sub02 from './pages/sub/Sub02'
import Sub03 from './pages/sub/Sub03'
import Sub04 from './pages/sub/Sub04'
import Sub05 from './pages/sub/Sub05'
import Sub06 from './pages/sub/Sub06'
import Sub07 from './pages/sub/Sub07'
import Sub08 from './pages/sub/Sub08'
import HomeRedirect from './pages/HomeRedirect'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/intro-01" element={<Intro01 />} />
      <Route path="/intro-02" element={<Intro02 />} />
      <Route path="/intro-03" element={<Intro03 />} />
      <Route path="/ob-01" element={<Ob01 />} />
      <Route path="/ob-02" element={<Ob02 />} />
      <Route path="/ob-03" element={<Ob03 />} />
      <Route path="/ob-04" element={<Ob04 />} />
      <Route path="/ob-05" element={<Ob05 />} />
      <Route path="/main-01" element={<Main01 />} />
      <Route path="/main-02" element={<Main02 />} />
      <Route path="/main-03" element={<Main03 />} />
      <Route path="/main-04" element={<Main04 />} />
      <Route path="/main-05" element={<Main05 />} />
      <Route path="/sub-01" element={<Sub01 />} />
      <Route path="/sub-02" element={<Sub02 />} />
      <Route path="/sub-03" element={<Sub03 />} />
      <Route path="/sub-04" element={<Sub04 />} />
      <Route path="/sub-05" element={<Sub05 />} />
      <Route path="/sub-06" element={<Sub06 />} />
      <Route path="/sub-07" element={<Sub07 />} />
      <Route path="/sub-08" element={<Sub08 />} />
      <Route path="*" element={<Navigate to="/intro-01" replace />} />
    </Routes>
  )
}
