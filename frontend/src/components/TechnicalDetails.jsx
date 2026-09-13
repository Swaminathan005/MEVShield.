import React, { useState, useEffect } from 'react';
import { getStatus } from '../api/api'; // We can reuse getStatus, but it doesn't have model info.
 // Actually, we have /api/health for model info.

 const TechnicalDetails = () => {
   const [modelInfo, setModelInfo] = useState(null);
   const [loading, setLoading] = useState(true);

   useEffect(() => {
     const fetchModelInfo = async () => {
       try {
         const response = await fetch('http://localhost:8000/api/health');
         if (response.ok) {
           const data = await response.json();
           setModelInfo(data);
         } else {
           console.error('Failed to fetch model info');
         }
       } catch (error) {
         console.error('Error fetching model info:', error);
       } finally {
         setLoading(false);
       }
     };

     fetchModelInfo();
   }, []);

   if (loading) {
     return <div className="technical-details">Loading technical details...</div>;
   }

   if (!modelInfo) {
     return <div className="technical-details">Failed to load technical details.</div>;
   }

   return (
     <section className="technical-details">
       <h2>TECHNICAL DETAILS</h2>
       <div className="details-grid">
         <div>
           <p><strong>MODEL</strong></p>
           <p>{modelInfo.model_name}</p>
         </div>
         <div>
           <p><strong>Detection Threshold</strong></p>
           <p>{modelInfo.threshold}</p>
         </div>
         <div>
           <p><strong>Training Data</strong></p>
           <p>2.44M transactions</p>
         </div>
         <div>
           <p><strong>Test Data</strong></p>
           <p>611K transactions</p>
         </div>
         <div>
           <p><strong>Live Replay</strong></p>
           <p>339K unseen transactions</p>
         </div>
         <div>
           <p><strong>PR-AUC</strong></p>
           <p>0.8591</p>
         </div>
         <div>
           <p><strong>ROC-AUC</strong></p>
           <p>0.9660</p>
         </div>
       </div>
     </section>
   );
 };

 export default TechnicalDetails;
