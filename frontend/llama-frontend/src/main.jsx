import 'bootstrap/dist/css/bootstrap.css';

import { createRoot } from 'react-dom/client'
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import './index.css'

import WebcamPage from './pages/WebcamPage';
import ReviewPage from './pages/ReviewPage';
import ResultPage from './pages/ResultPage';

const router = createBrowserRouter([
  {
    path: "/",
    children: [
      {
        path: "/",
        element: <WebcamPage />
      },
      {
        path: "/review",
        element: <ReviewPage />
      },
      {
        path: "/result/:streamId",
        element: <ResultPage />
      }
    ]
  },
]);

createRoot(document.getElementById('root')).render(
  <RouterProvider router={router} />
)
