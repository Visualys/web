#!/usr/bin/python
import ephem
from datetime import datetime, timedelta
tz = int((datetime.now()-datetime.utcnow()).seconds/3600)

date = ephem.Date(datetime.utcnow())
nnm = ephem.next_new_moon(datetime.utcnow())
pnm = ephem.previous_new_moon(datetime.utcnow())
lunation = (date-pnm)/(nnm-pnm)
if lunation<.5:
  trend = '/'
  perc_phase = lunation*2
else:
  trend = '\\'
  perc_phase = (1-lunation)*2
  
print('pourcentage cycle entier : %s' % round(lunation*100,2))
print('phase lunaire : %s (%s)' % (round(perc_phase*100,1), trend))


------------------------------------------------------------------------------------------------
// Javascript part
------------------------------------------------------------------------------------------------

cycle = .2626;

var o = document.createElement('canvas')
move(o, [50,50,100,100]);
document.body.appendChild(o);
o.width=210; o.height=210;
c = o.getContext('2d');
c.translate(o.width/2, o.height/2);


function draw(){
drawing = new Image();
drawing.src = "C:/Users/105053823/OneDrive - Baker Hughes/_archivage/reVis/Web_Coding/Javascript_Editor/moon.png"; // can also be a remote URL e.g. http://
drawing.onload = function() {
c.clearRect(-o.width/2,-o.width/2,210,210);
   c.drawImage(drawing,-100,-100, 200, 200);

  c.lineWidth = 2;
  c.strokeStyle = 'rgba(10,10,10,.5)'

  c.fillStyle=fillStyle='rgba(10,10,10,.80)';
  if(cycle<.5)
    {pL=-1; pR=1-4*cycle}
    else
    {pL=3-4*cycle;pR=1}

  c.beginPath();
  c.moveTo(0,-100);
  for(var a=Math.PI/2;a<Math.PI*1.5;a+=.1){
    c.lineTo(-pL*100*Math.cos(a), -100*Math.sin(a) )
    }
  c.lineTo(0,100);
  for(var a=Math.PI*1.5;a<Math.PI*5/2;a+=.1){
    c.lineTo(pR*100*Math.cos(a), -100*Math.sin(a) )
    }

  c.fill()

  }
};

draw()
